# OCI Free VM with Volume

This Terraform project provisions a free-tier Oracle Cloud Infrastructure (OCI) virtual machine (VM) with an attached block volume. It is designed to help users quickly deploy and manage a free-tier VM instance with persistent storage.

## Features
- Provisions a free-tier VM instance in OCI.
- Attaches a block volume for persistent storage.
- Configurable through `terraform.tfvars`.
- Uses `cloud_init.yaml` for instance initialization.

## Prerequisites
1. Install [Terraform](https://www.terraform.io/downloads).
2. Set up an OCI account and generate API keys.
3. Configure your OCI CLI with the required credentials.

## Usage

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd oci_free_vm_with_volume
   ```

2. **Configure Variables**
   Update the `terraform.tfvars` file with your OCI credentials and desired configuration:
   ```hcl
   tenancy_ocid = "<your-tenancy-ocid>"
   user_ocid    = "<your-user-ocid>"
   region       = "<your-region>"
   compartment_ocid = "<your-compartment-ocid>"
   ssh_public_key = "<path-to-your-ssh-public-key>"
   ```

3. **Initialize Terraform**
   Run the following command to download the required providers:
   ```bash
   terraform init
   ```

4. **Plan the Deployment**
   Preview the changes that Terraform will make:
   ```bash
   terraform plan
   ```

5. **Apply the Configuration**
   Deploy the resources to OCI:
   ```bash
   terraform apply
   ```
   Confirm the prompt with `yes`.

6. **Access the VM**
   Use the public IP address of the VM to SSH into it:
   ```bash
   ssh -i <path-to-private-key> opc@<vm-public-ip>
   ```

## Cleanup
To destroy the resources created by this project, run:
```bash
terraform destroy
```
Confirm the prompt with `yes`.

## File Structure
- `main.tf`: Defines the OCI resources to be provisioned.
- `variables.tf`: Declares input variables for the project.
- `terraform.tfvars`: Contains user-specific variable values.
- `cloud_init.yaml`: Specifies initialization scripts for the VM.
- `.terraform.lock.hcl`: Tracks provider versions.

## Notes
- Ensure that your OCI account has sufficient free-tier resources available.
- Modify `cloud_init.yaml` to customize the VM initialization process.
