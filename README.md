1. Create image:
    ```docker build -t vocabulary-challenger .```  
2. Run the container:
    ```docker run --name vocab_container --env-file .env -it -v ${pwd}/src:/app vocabulary-challenger```  
3. Start the container for interacting:
    ```docker start -i vocab_container```  