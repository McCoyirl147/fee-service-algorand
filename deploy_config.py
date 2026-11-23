import logging
import os

import algokit_utils

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy() -> None:
    from smart_contracts.artifacts.fee_service.fee_service_client import (
        FeeServiceFactory,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    # DevMode LocalNet produces a block per transaction; disable param cache
    # so consecutive calls do not reuse first_valid and collide on txid.
    algorand.set_suggested_params_cache_timeout(0)
    deployer_ = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        FeeServiceFactory, default_sender=deployer_.address
    )

    # factory.deploy() uses the Indexer to find an existing app of the same name.
    # If the Indexer is unavailable (as on some LocalNet setups), create a new
    # instance directly through algod.
    created = False
    try:
        app_client, result = factory.deploy(
            on_update=algokit_utils.OnUpdate.AppendApp,
            on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        )
        if result.operation_performed in [
            algokit_utils.OperationPerformed.Create,
            algokit_utils.OperationPerformed.Replace,
        ]:
            created = True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "factory.deploy() could not use the Indexer (%s); "
            "creating a new FeeService app via algod instead",
            exc,
        )
        app_client, _result = factory.send.create.bare()
        created = True

    # Default 0: callers pay the creator directly, so the app account needs no ALGO.
    fund_algo = float(os.environ.get("APP_FUND_ALGO", "0"))
    if created and fund_algo > 0:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=fund_algo),
                sender=deployer_.address,
                receiver=app_client.app_address,
            )
        )

    logger.info(
        f"Deployed {app_client.app_name} ({app_client.app_id}). "
        "FeeService does not need ALGO in the app account; callers pay the creator directly."
    )
