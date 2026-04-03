# Pipeline

1. Congressus sends a webhook call to our API about a change in the administration.
2. The pending changed is pushed into the Directory Queue.
3. Sync pops the pending change from the queue.
4. Sync changes the Directory based on the pending change information and **information from Congressus**.
5. Sync changes the ACL to match the changed Directory.
