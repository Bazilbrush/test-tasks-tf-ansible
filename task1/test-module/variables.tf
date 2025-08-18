variable "storage_account_name" {
  
}
variable "resource_group_name" {
  
}
variable "location" {
  default = "UK South"
}

variable "queue_names" {
  description = "List of queue names"
  type        = list(string)
  default     = []
}