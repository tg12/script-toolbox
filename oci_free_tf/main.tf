terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 7.10.0"
    }
  }
}

provider "oci" {
  region       = var.region
  tenancy_ocid = var.tenancy_ocid
  user_ocid    = var.user_ocid
  fingerprint  = var.fingerprint
  private_key  = file(var.private_key_path)
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

data "oci_core_images" "ubuntu_image" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = var.shape
}

output "ubuntu_images" {
  value = data.oci_core_images.ubuntu_image.images
}

resource "oci_core_virtual_network" "vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "free-tier-vcn"
  cidr_block     = "10.0.0.0/16"
  dns_label      = "vcn"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "free-tier-igw"
}

resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "free-tier-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

resource "oci_core_security_list" "sec_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "free-tier-sec-list"

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"

    tcp_options {
      min = 22
      max = 22
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_virtual_network.vcn.id
  cidr_block                 = "10.0.1.0/24"
  display_name               = "free-tier-subnet"
  dns_label                  = "subnet"
  route_table_id             = oci_core_route_table.rt.id
  security_list_ids          = [oci_core_security_list.sec_list.id]
  prohibit_public_ip_on_vnic = false
}


resource "oci_core_instance" "vm" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  shape               = var.shape
  display_name        = "free-tier-vm"

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    assign_public_ip = true
    display_name     = "primaryvnic"
    hostname_label   = "freevm"
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode(templatefile("cloud_init.yaml", {}))
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu_image.images[0].id
    boot_volume_size_in_gbs = 50
  }
}

# resource "oci_core_volume" "persistent_volume" {
#   availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
#   compartment_id      = var.compartment_ocid
#   display_name        = "free-tier-volume"
#   size_in_gbs         = 50
# }

# resource "oci_core_volume_attachment" "attach_persistent_volume" {
#   instance_id     = oci_core_instance.vm.id
#   volume_id       = oci_core_volume.persistent_volume.id
#   attachment_type = "iscsi"
#   device          = "/dev/oracleoci/oraclevdb"
# }

output "vm_public_ip" {
  value = oci_core_instance.vm.public_ip
}

// To SSH into the instance, use the following command:
// ssh -i <path_to_private_key> opc@${oci_core_instance.vm.public_ip}

