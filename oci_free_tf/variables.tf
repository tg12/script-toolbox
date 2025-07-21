
variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "compartment_ocid" {}
variable "region" {}
variable "ssh_public_key_path" {}

# Available shapes for the free tier:
# VM.Standard.E2.1.Micro
# VM.Standard.A1.Flex

variable "shape" {
  default = "VM.Standard.E2.1.Micro"
}

variable "ocpus" {
  default = 1
}

variable "memory" {
  default = 1
}
