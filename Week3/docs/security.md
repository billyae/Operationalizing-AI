# Security Documentation

Covers authentication, data protection, and best practices.

## 1. Authentication & Authorization

- **AWS IAM**  
  - Use scoped IAM credentials with least privileges (only `bedrock:InvokeModel` and `bedrock:ListModels`).
- **App-Level**  
  - `user_id` is derived by hashing the AWS Access Key (no PII exposure).

## 2. Secrets Management

- **Environment Variables**  
  - Never commit AWS keys to source control.
  - Consider **AWS Secrets Manager** or **Vault** for production.
- **Rotation**  
  - Rotate IAM keys regularly (e.g. every 90 days).

## 3. Transport Security

- Expose all APIs over **HTTPS** (TLS 1.2+).  
- Terminate TLS at the ingress/load balancer.

## 4. Input Validation

- Sanitize and validate all incoming JSON fields in FastAPI schemas (`pydantic` models).  
- Reject malformed or excessively large payloads.

## 5. Audit Logging & Monitoring

- **Immutable Logs**  
  - Maintain write-only logs in a secure DB (consider WORM storage).  
- **Alerting**  
  - Monitor error rates and latency spikes (e.g. via Prometheus/Grafana).

## 6. Data Protection

- **Encryption at Rest**  
  - Encrypt `audit_logs.db` or migrate to an encrypted database.  
- **Access Controls**  
  - Lock down database file permissions (e.g. `chmod 600 audit_logs.db`).

## 7. CORS & Network Policies

- Restrict API origins via CORS rules in FastAPI middleware.  
- Use network ACLs/security groups to limit inbound access to known IPs.

---