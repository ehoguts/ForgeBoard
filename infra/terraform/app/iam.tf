resource "aws_iam_role" "app" {
  name = "${local.name}-app"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "${local.name}-runtime"
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadOnlyApplicationCredential"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = aws_secretsmanager_secret.application_database.arn
      },
      {
        Sid      = "ReadOnlyReleaseBundles"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = "${aws_s3_bucket.releases.arn}/releases/*"
      },
      {
        Sid      = "ListOnlyReleasePrefix"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.releases.arn
        Condition = {
          StringLike = { "s3:prefix" = ["releases", "releases/*"] }
        }
      },
      {
        # These SSM APIs do not support resource-level permissions. Do not replace
        # this small API set with ssm:* or the broader managed instance policy.
        Sid      = "RegisterThisManagedInstance"
        Effect   = "Allow"
        Action   = "ssm:UpdateInstanceInformation"
        Resource = "*"
      },
      {
        Sid    = "SSMAgentControlAndDataChannels"
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      },
      {
        Sid    = "ReadOnlySupportedSSMDocuments"
        Effect = "Allow"
        Action = ["ssm:GetDocument", "ssm:DescribeDocument"]
        Resource = [
          "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}::document/AWS-RunShellScript",
          "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}::document/AWS-StartPortForwardingSessionToRemoteHost",
          "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}:${var.aws_account_id}:document/SSM-SessionManagerRunShell"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${local.name}-app"
  role = aws_iam_role.app.name
}
