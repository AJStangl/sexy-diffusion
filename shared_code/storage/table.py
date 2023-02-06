import logging
import os

from azure.core.paging import ItemPaged
from azure.data.tables import TableClient, TableEntity
from azure.data.tables import TableServiceClient

logger = logging.getLogger(__name__)
logging.getLogger("azure.storage").setLevel(logging.WARNING)


class TableAdapter:
	def __init__(self):
		self.connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]

	def get_table_service_client(self) -> TableServiceClient:
		service = TableServiceClient.from_connection_string(conn_str=self.connection_string)
		return service

	def get_table_client(self, table_name: str) -> TableClient:
		service: TableServiceClient = self.get_table_service_client()
		return service.get_table_client(table_name=table_name)

	def upsert_entity_to_table(self, table_name: str, entity: dict):
		table_client: TableClient = self.get_table_client(table_name=table_name)
		table_client.upsert_entity(entity=entity)
		return

	def get_all_entities(self, table_name: str) -> list[dict]:
		table_client: TableClient = self.get_table_client(table_name=table_name)
		entities: ItemPaged[TableEntity] = table_client.list_entities()
		return list(entities)

	def get_table_client_instance(self, table_name: str) -> TableClient:
		service: TableServiceClient = self.get_table_service_client()
		return service.get_table_client(table_name=table_name)

	def get_entity(self, table_name: str, partition_key: str, row_key: str) -> TableEntity:
		table_client: TableClient = self.get_table_client(table_name=table_name)
		entity: TableEntity = table_client.get_entity(partition_key=partition_key, row_key=row_key)
		return entity
