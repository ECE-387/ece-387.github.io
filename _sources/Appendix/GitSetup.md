
# Git Repo Setup


## Purpose
Setup GIT repositories and access on the **Master**.

```{note}
Don’t worry if it doesn’t work right. If everything did, you’d be out of a job.
```

(CreateRepo)=
### Create a Repository within the GitHub Classroom

1. If you don’t already have a <a href="https://github.com/" target="_blank">GitHub</a> account, create one. It’s best if your username is something identifiable (e.g., `stanbaek`).  

1. Once your account is ready, go to the <a href="https://classroom.github.com/a/gHikuWHu" target="_blank">ECE387 Classroom</a>.  

1. Your afacademy email address has been preloaded to make joining easy. While I prefer your school email address, you may use another email if desired. For this, click `Skip to the next step`:  

    ```{image} ./figures/GitClassroom_SelectIdentifier.png  
    :width: 480  
    :align: center  
    ```  
    <br>  

1. Select `Accept this assignment`.  

1. Navigate to your repository and note the repository URL. Save this link—it’s the easiest way to check if your repository is updated.  

1. Go to `Settings` and change your repository name to `ece387-lastname` (e.g., `ece387-baek`).  Use all lowercase, your last name only, and include the dash.

    ```{important}  
    Please name your repository `ece387-lastname` (all lowercase, with a dash). This makes it easier for instructors to locate your repository. If not, points will be deducted.  
    ```  

(GitHubSSHKey)=
## Set Up GitHub SSH Key on Master  

This section assumes you already have a GitHub account.  

1. Create an SSH key for your GitHub account by running the following command. Use the same email as your GitHub login:  

    ```bash  
    $ cd  
    $ ssh-keygen -t ed25519 -C "your_email@email.com"  
    ```  

1. When prompted to specify a file path, press `Enter` to accept the default location (`~/.ssh/id_ed25519`).  

1. Start the ssh-agent in the background and add your SSH private key:  

    ```bash  
    $ eval "$(ssh-agent -s)"  
    $ ssh-add ~/.ssh/id_ed25519  
    ```  

1. Open the public key using your favorite terminal-based text editor. This step is easier via an SSH connection from a GUI-based desktop machine, as it allows you to copy the public key to your GitHub account:  

    ```bash  
    $ nano ~/.ssh/id_ed25519.pub  
    ```  

1. Copy the entire contents of the file. Maximize the window to ensure you don’t miss anything, including the GitHub email.  

1. Open a web browser and log in to your GitHub account.  

1. In the top-right corner of any page, click your profile photo, then select **Settings**:  

    ```{image} ./figures/ssh1.png  
    :width: 180  
    :align: center  
    ```  
    <br>  

1. In the settings sidebar, click **SSH and GPG keys**:  

    ```{image} ./figures/ssh2.png  
    :width: 180  
    :align: center  
    ```  
    <br>  

1. Click **New SSH key**:  

    ```{image} ./figures/ssh3.png  
    :width: 600  
    :align: center  
    ```  
    <br>  

1. In the `Title` field, provide a descriptive label for the key, such as `master0`.  

1. Paste the copied key (from the `.pub` file) into the `Key` field.  

1. Click **Add SSH key** to save it.  

(CloneRepo)=
## Clone Repository to Your Master  

1. On the **Master**, open your GitHub repository and copy the repository address using the **SSH** mode:  

    ```{image} ./figures/GitClone.png  
    :width: 600  
    :align: center  
    ```  
    <br>  

1. Open a terminal and create a workspace source folder:  
    ```bash  
    $ mkdir -p ~/master_ws/src/  
    $ cd ~/master_ws/src  
    ```  

1. Clone your repository:  
    ```bash  
    $ git clone git@github.com:ECE387/ece387-lastname.git  
    ```  

1. Move into your repository you just cloned:  
    ```bash  
    $ cd ece387-lastname  
    ```  

1. Update your Git email address and name:  
    ```bash  
    $ git config user.email "you@example.com"  
    $ git config user.name "FirstName LastName"  
    ```  

1. create a directory named `lab1` and move into it.

1. Create an empty file called `COLCON_IGNORE`. This file tells colcon to ignore this directory when building ROS packages, which prevents accidental compilation of files that aren't meant to be part of your workspace.

1. Run the following command to append your full name and section to a file named `README.md`. Since the file does not exist, it will be created automatically:
    ```bash  
    $ echo "# Your full name, Section" >> README.md  
    ```  

1. Verify that the file was created correctly by running:  
    ```bash  
    $ cat README.md  
    ```  
    If the file was created successfully, you should see output similar to the following:
    ```{image} ./figures/GitCreateReadmeFile.png  
    :width: 400  
    :align: center  
    ```  
    <br>  
1. Commit and push your changes to your GitHub repository:
    ```bash  
    $ git add -A 
    $ git commit -m"initial commit"
    $ git push  
    ```  

