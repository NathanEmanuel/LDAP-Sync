# Pipeline

1. Congressus sends a webhook call to our API about a Change in the administration.
2. The pending Change is pushed into the Directory Queue.
3. Sync pops the pending Change from the Queue.
4. Sync changes the Directory based on the pending Change information and **information from Congressus**.
5. Sync changes the ACL to match the changed Directory.
