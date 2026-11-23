# fee-service-algorand

A simple paid-service smart contract written in **Algorand Python** (PuyaPy, built with AlgoKit) and live on Algorand **mainnet**.

- **Mainnet App ID:** `3780553713`. You can view it on [Lora](https://lora.algokit.io/mainnet/application/3780553713).
- Each `service` call must include a payment of at least **0.1 ALGO** sent straight to the app **creator**. The call returns the **square** of the input number.

## Methods

| Method | What it does |
| --- | --- |
| `service(pay payment, uint64 value) uint64` | Checks the grouped payment: the receiver is the creator, the amount is at least `fee`, the sender is the caller, and there is no rekey or close-remainder. It then returns `value * value` and updates `last_result`, `calls` and `total_fees`. |
| `get_total_fees() uint64` | Read-only. Returns the total fees paid, in microAlgos. |
| `get_calls() uint64` | Read-only. Returns the number of successful service calls. |
| `get_fee() uint64` | Read-only. Returns the current fee, in microAlgos (default 100000). |
| `set_fee(uint64)` | Creator only. Changes the fee. |

Create is a bare NoOp. Because the fee goes directly to the creator, the contract needs no inner transactions and the app account needs no funding.

## Files

- `contract.py` is the contract source.
- `FeeService.arc56.json` is the ARC-56 app spec. Upload it to Lora App Lab to deploy your own copy.
- `FeeService.approval.teal` and `FeeService.clear.teal` are the compiled TEAL.
- `deploy_config.py` is an AlgoKit deploy script. `fee_service_test.py` holds the unit tests (algopy_testing).

## Deploy your own copy

1. Open [Lora App Lab on mainnet](https://lora.algokit.io/mainnet/app-lab) (or testnet) and connect your wallet.
2. Choose **Create App Interface**, then **Deploy new app**, and upload `FeeService.arc56.json`.
3. Pick the bare create (NoOp) and approve the transaction in your wallet.
4. Call `service` with a payment of 0.1 ALGO to *your* creator address and a `value`.

While you own the app, about 0.314 ALGO is locked as minimum balance (0.1 for the account, 0.1 for the app, and 4 × 0.0285 for the global ints).

With AlgoKit, drop `contract.py` into an Algorand Python project under `smart_contracts/fee_service/` and run `algokit project run build`.

## Disclaimer

This is a learning example. It has **not been audited**. Use it at your own risk.

## License

MIT
