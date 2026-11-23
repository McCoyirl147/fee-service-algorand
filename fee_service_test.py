from collections.abc import Iterator

import pytest
from algopy import UInt64
from algopy_testing import AlgopyTestContext, algopy_testing_context

from smart_contracts.fee_service.contract import FeeService


@pytest.fixture()
def context() -> Iterator[AlgopyTestContext]:
    with algopy_testing_context() as ctx:
        yield ctx


def _payment(
    context: AlgopyTestContext,
    *,
    amount: int = 100_000,
    receiver: object | None = None,
    sender: object | None = None,
    rekey_to: object | None = None,
    close_remainder_to: object | None = None,
):
    fields: dict[str, object] = {
        "amount": amount,
        "receiver": context.default_sender if receiver is None else receiver,
        "sender": context.default_sender if sender is None else sender,
    }
    if rekey_to is not None:
        fields["rekey_to"] = rekey_to
    if close_remainder_to is not None:
        fields["close_remainder_to"] = close_remainder_to
    return context.any.txn.payment(**fields)


def test_initial_state(context: AlgopyTestContext) -> None:
    contract = FeeService()
    assert contract.get_total_fees() == 0
    assert contract.get_calls() == 0
    assert contract.get_fee() == 100_000
    assert contract.last_result == 0


def test_service_success(context: AlgopyTestContext) -> None:
    contract = FeeService()
    result = contract.service(_payment(context), UInt64(5))

    assert result == 25
    assert contract.last_result == 25
    assert contract.get_calls() == 1
    assert contract.get_total_fees() == 100_000


def test_service_records_overpayment(context: AlgopyTestContext) -> None:
    contract = FeeService()
    result = contract.service(_payment(context, amount=250_000), UInt64(12))

    assert result == 144
    assert contract.get_calls() == 1
    assert contract.get_total_fees() == 250_000


def test_underpayment_rejected(context: AlgopyTestContext) -> None:
    contract = FeeService()

    with pytest.raises(AssertionError, match="payment is less than the required fee"):
        contract.service(_payment(context, amount=99_999), UInt64(5))

    assert contract.get_calls() == 0
    assert contract.get_total_fees() == 0


def test_wrong_receiver_rejected(context: AlgopyTestContext) -> None:
    contract = FeeService()
    other = context.any.account()

    with pytest.raises(AssertionError, match="fee must be paid to the creator"):
        contract.service(_payment(context, receiver=other), UInt64(5))

    assert contract.get_calls() == 0
    assert contract.get_total_fees() == 0


def test_wrong_sender_rejected(context: AlgopyTestContext) -> None:
    contract = FeeService()
    other = context.any.account()

    with pytest.raises(AssertionError, match="payment sender must be the caller"):
        contract.service(_payment(context, sender=other), UInt64(5))

    assert contract.get_calls() == 0


def test_rekey_rejected(context: AlgopyTestContext) -> None:
    contract = FeeService()
    other = context.any.account()

    with pytest.raises(AssertionError, match="payment must not rekey"):
        contract.service(_payment(context, rekey_to=other), UInt64(5))


def test_close_remainder_rejected(context: AlgopyTestContext) -> None:
    contract = FeeService()
    other = context.any.account()

    with pytest.raises(AssertionError, match="payment must not close remainder"):
        contract.service(_payment(context, close_remainder_to=other), UInt64(5))


def test_overflow_guard(context: AlgopyTestContext) -> None:
    contract = FeeService()

    with pytest.raises(AssertionError, match="value too large to square safely"):
        contract.service(_payment(context), UInt64(4_294_967_296))

    max_safe = contract.service(_payment(context), UInt64(4_294_967_295))
    assert max_safe == 4_294_967_295 * 4_294_967_295
    assert contract.get_calls() == 1


def test_set_fee_by_creator(context: AlgopyTestContext) -> None:
    contract = FeeService()
    contract.set_fee(UInt64(50_000))
    assert contract.get_fee() == 50_000

    result = contract.service(_payment(context, amount=50_000), UInt64(3))
    assert result == 9
    assert contract.get_total_fees() == 50_000


def test_set_fee_rejects_non_creator(context: AlgopyTestContext) -> None:
    contract = FeeService()
    other = context.any.account()

    with context.txn.create_group(active_txn_overrides={"sender": other}):
        with pytest.raises(AssertionError, match="only the creator can set the fee"):
            contract.set_fee(UInt64(1))

    assert contract.get_fee() == 100_000
