from algopy import ARC4Contract, Global, Txn, UInt64, gtxn
from algopy.arc4 import abimethod

class FeeService(ARC4Contract):
    """A paid square-calculation service. The fee is paid to the creator."""

    def __init__(self) -> None:
        self.total_fees = UInt64(0)
        self.calls = UInt64(0)
        self.last_result = UInt64(0)
        self.fee = UInt64(100_000)  # 0.1 ALGO, in microAlgos

    @abimethod()
    def service(self, payment: gtxn.PaymentTransaction, value: UInt64) -> UInt64:
        """Accept a fee payment, return value squared, and record the call."""
        assert payment.receiver == Global.creator_address, "fee must be paid to the creator"
        assert payment.amount >= self.fee, "payment is less than the required fee"
        assert payment.sender == Txn.sender, "payment sender must be the caller"
        assert payment.rekey_to == Global.zero_address, "payment must not rekey"
        assert payment.close_remainder_to == Global.zero_address, "payment must not close remainder"
        assert value <= UInt64(4_294_967_295), "value too large to square safely"

        result = value * value
        self.last_result = result
        self.calls += 1
        self.total_fees += payment.amount
        return result

    @abimethod(readonly=True)
    def get_total_fees(self) -> UInt64:
        """Return accumulated fees paid, in microAlgos."""
        return self.total_fees

    @abimethod(readonly=True)
    def get_calls(self) -> UInt64:
        """Return how many successful service calls have been made."""
        return self.calls

    @abimethod(readonly=True)
    def get_fee(self) -> UInt64:
        """Return the current required fee, in microAlgos."""
        return self.fee

    @abimethod()
    def set_fee(self, new_fee: UInt64) -> None:
        """Update the required fee. Only the app creator can call this."""
        assert Txn.sender == Global.creator_address, "only the creator can set the fee"
        self.fee = new_fee
