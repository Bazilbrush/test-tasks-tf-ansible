output "storage_account_id" {
  description = "The id of the storage acc"
  value       = azurerm_storage_account.this.id
}

output "queue_urls" {
  description = "List of created queue urls."
  value       = [for queue in azurerm_storage_queue.queues : queue.name]
}