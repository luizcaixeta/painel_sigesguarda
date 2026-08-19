from mlflow import MlflowClient

def promote_version(
        model_name: str,
        alias_name: str,
        version: str,
    ) -> None:

    client = MlflowClient()

    return client.set_registered_model_alias(
        name=model_name,
        alias=alias_name,
        version=str(version)
    )