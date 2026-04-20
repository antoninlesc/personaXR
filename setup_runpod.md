# Setting up RunPod and Running the pipeline



### Tailscale
    1. tailscale up

    2. tailscale serve --http 80 127.0.0.1:8080

From the second command, you will get an URL. Use that to communicate between your frontend and backend.

### GitHub repo
Clone the Repo in the /workplace folder as it is the only one that will be saved if you terminate the pod.

    1. git clone

    2. Create the .env file

### Vim (To edit files)
    1. sudo apt-get update
    2. sudo apt-get install vim
