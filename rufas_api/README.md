# Documentation for the API service for RuFaS

# Sequence diagrams
## Farm service:
This service is for launching the entire farm simulations using `RuFaS` class `TaskManager`. In such a case, the runtime
is relatively long (> 2 mins) and the service needs to be asynchronous.

```mermaid
sequenceDiagram
    title Rufas API
    autonumber
    actor user as API Client
    participant web_worker as Web Worker
    participant task_broker as Task Broker
    participant task_worker as Task Worker

    participant rufas_wrapper as Rufas Wrapper
    participant rufas as Rufas

    %% web worker
    user ->> web_worker: Requests <something> with parameters
    web_worker --> rufas_wrapper: Validate parameters
    Note left of web_worker: Validation Process steps<br>could be skipped<br>if too slow
    rufas_wrapper --> web_worker: Confirms
    web_worker ->> task_broker: Enqueue task <something task> with parameters
    task_broker ->> web_worker: Returns <task_id>
    web_worker ->> user: Response with <task_id>
    user ->> user: Waits
    user ->> web_worker: Request task status with <task_id>
    web_worker ->> task_broker: Request task status
    task_broker ->> web_worker: Return task status "not completed"
    web_worker ->> user: Returns response with status  "not completed"
    user ->> user: Waits

    task_broker ->> task_worker: Start task <something task>
    task_worker ->> rufas_wrapper: Provide parameters
    
    rufas_wrapper ->> rufas_wrapper: Preprocess:<br>Validation and convert to Rufas format
    
    rufas_wrapper ->> rufas: Process
    rufas ->> rufas_wrapper: Output results

    rufas_wrapper ->> rufas_wrapper: Post-processing: Extract results from output
    rufas_wrapper ->> rufas_wrapper: Cleanup (temp data)  

    rufas_wrapper ->> task_worker: Return result

    task_worker ->> task_broker: Return result    
    
    user ->> web_worker: Request task status with <task_id>
    web_worker ->> task_broker: Request task status
    task_broker ->> web_worker: Return task success and data
    web_worker ->> user: Returns response with success and data


    user ->> user: Do something with the data (ex: store to database)
```

## Only rations service:
This service is only for launching the calculations of animal rations. In such a case, the runtime is short and the
service is synchronous.

```mermaid
sequenceDiagram
    title Rufas API - rations
    autonumber
    actor user as API Client
    participant web_worker as Web Worker
    participant rufas_wrapper as Rufas Wrapper
    participant rufas as Rufas

    %% web worker
    user ->> web_worker: Requests <something> with parameters
    web_worker -> rufas_wrapper: Validate parameters
    Note left of web_worker: Validation Process steps<br>could be skipped<br>if too slow
    rufas_wrapper -> web_worker: Confirms
    
    

    web_worker ->> rufas_wrapper: Start task <something task> with parameters
    
    rufas_wrapper ->> rufas_wrapper: Preprocess:<br>Validation and convert to Rufas format
    
    rufas_wrapper ->> rufas: Process
    rufas ->> rufas_wrapper: Output results

    rufas_wrapper ->> rufas_wrapper: Post-processing: Extract results from output
    rufas_wrapper ->> rufas_wrapper: Cleanup (temp data)  

    rufas_wrapper ->> web_worker: Return result
    web_worker ->> user: Returns response with success and data


    user ->> user: Do something with the data (ex: store to database)
```