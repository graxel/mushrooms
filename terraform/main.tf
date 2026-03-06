variable "branch" {}

resource "aws_instance" "server" {
  ami = "ami-ubuntu"  # Your AMI
  instance_type = "t3.micro"
  tags = { Name = "server-${var.branch}" }
}

resource "aws_db_instance" "postgres" {
  # ... your DB config
  username = "mluser"
  password = random_password.db.result
}

resource "random_password" "db" { length = 16 }

output "server_ip" { value = aws_instance.server.public_ip }
output "pg_host" { value = aws_db_instance.postgres.endpoint }
output "pg_user" { value = aws_db_instance.postgres.username }
output "pg_pass" { value = aws_db_instance.postgres.password }
output "pg_db" { value = aws_db_instance.postgres.name }
