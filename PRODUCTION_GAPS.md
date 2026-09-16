# External production validation still required

These items cannot be truthfully completed inside the local build alone:

- Real domain and TLS certificate
- Real transactional SMTP delivery
- Off-host backup and restore drill
- Managed database decision/migration if PostgreSQL is required
- Independent penetration test
- Legal review for each launch jurisdiction
- Pilot usability evidence from real children, parents and teachers
- Device/browser matrix on physical hardware

The release gate intentionally keeps these separate from internal QA.
