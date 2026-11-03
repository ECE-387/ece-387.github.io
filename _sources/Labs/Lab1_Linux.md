# 🔬 Lab1: Linux

## 📌 Objectives
- Students should be able to use commands like `ls`, `pwd`, and `cd` to explore directories, navigate using relative and absolute paths, and understand the structure of the Linux filesystem.  
- Students should be able to create files and directories using `touch` and `mkdir`, modify file timestamps, and delete items using `rm` and `rmdir`, including handling hidden and non-empty directories.  
- Students should be able to use advanced `ls` options such as `-lah` to display detailed file and directory information, including permissions, ownership, and sizes, and recognize hidden files.  
- Students should be able to use features like tab autocompletion, output redirection (`>`), and pipes (`|`) to streamline their workflow and combine commands for advanced functionality.  
- Students should be able to view system information and processes using commands like `ps`, `top`, and `cat /proc/cpuinfo`, and perform system actions such as shutting down or restarting from the command line.  

## Linux Commands 🐧
During class, we covered several basic Linux commands. In this lab, we will get hands-on practice with those commands.

1. To log in the Master computer, use your login ID, starting with `a27-`. 
1. Click the Terminal icon on the Dock to open a terminal and practice commands.

    ```{image} ./figures/Lab1_Terminal.png
    :width: 300
    :align: center
    ```
    <br>

1. You can select an open terminal and use `Ctrl + Shift + n` to open a new terminal window or `Ctrl + Shift + t` to add a new tab to the current terminal.

1. When observing the terminal (or Shell) you will notice the following
    - Syntax: `username@hostname:`(e.g., on the master: `a27-yy@masterX:`, on the robot: `pi@robotX`)
    - Current working directory: Represented as `~`, which refers to the user's home directory. 
    - Prompt: The `$` character followed by a blinking cursor, which indicates the terminal is active and ready for commands.

### Using Filesystem

To master Linux, it's crucial to understand the filesystem and become comfortable with the Terminal (or shell). While the command line may feel intimidating at first, regular practice will make it second nature.


1. **View Directory Contents**: Enter `ls` to see the contents of the current directory. You'll see directories like Desktop, Documents, and Downloads. Color coding helps identify types: directories are blue, files are white, executable files are bright green, and archived files are red. For now, just note that directories are blue and files are white.

1. **Display Current Directory Path**: Enter `pwd` to display the path of the current directory. This will show your home directory path, such as `/home/students/a27-m0`.

1. **Change Directory**: To move from your home directory to the Downloads directory, enter `cd Downloads`. The `cd` command stands for "change directory." Enter `ls` again to view the files inside the Downloads directory.

1. **Navigate to Parent Directory**: Use `cd ..` to navigate back to the home directory. In Linux, two dots `..` refer to the directory above (the parent directory). A single dot `.` refers to the current directory. While you don't use `cd .` to switch to the current directory, knowing this can be useful for some commands.

1. **Root Directory**: The root directory is always `/`. Enter `ls /` to list the contents of the root directory, and `cd /` to switch to the root directory. It's important to understand the difference between `ls Downloads` and `ls /Downloads`. The first command lists the contents of the Downloads directory within the current directory, while the second tries to list a Downloads directory directly under the root, which usually doesn't exist.

1. **View Root Directory Contents**: Enter `cd /` followed by `ls` to view the files inside the root directory.

1. **Return to Home Directory**: Enter `cd` to move back to your home directory. Note that `cd` is equivalent to `cd ~`.

1. **Complex Paths**: The `ls` and `cd` commands can also be used with more complex paths. For example, enter `ls /opt/ros/jazzy` to view the contents of the "jazzy" directory inside "ros," which is inside "opt." Switch to this directory using `cd /opt/ros/jazzy`. To move back up three parent directories, use `cd ../../..`.

1. **Autocomplete**: Type `cd /o` followed by the tab key. It will autocomplete to `cd /opt/`. Press the tab key again to see options like `google` and `ros`. Type `r` and press the tab key to choose `ros`, then press the tab key again to choose `jazzy` as it is the only directory inside `ros`.

    ```{image} ./figures/Lab1_Autocomplete.gif
    :width: 520
    :align: center
    ```
    <br>

### Listing Files

Using the desktop GUI to list and move files is easier than using the Terminal and keyboard, but it's an important skill that you’ll appreciate as you advance with ROS and Linux.

1. **Basic Listing**: We've already looked at `ls`, which lists the files in the working directory. You're more likely to use a command like `ls -lah`. The bit after the command (the `-lah`) is known as the argument. This option modifies the behavior of the command. The `-l` argument lists files and directories in "long" format. Each file and directory is now on a single line, and before each file is a lot of text. First, you'll see letters and dashes, like `drwxr-xr-x`. These are `permissions`, and we briefly discussed in class.

    ```{image} ./figures/Lab1_ls-lah.png
    :width: 520
    :align: center
    ```
    <br>

1. **File Count**: After the permission letters, there's a single number. This is the number of files in the item. If it's a file, it will be 1, but if it's a directory, it will be at least 2. Each directory contains two hidden files: one with a single dot (`.`) and one with two dots (`..`). Directories containing files or other directories will have a higher number.

1. **Owner and Group**: Next, you'll see your username twice on each line. The first is the owner of the file, and the second is the group. Typically, these will be the same, and you'll see either `root` or your username. You can enter `ls -l /` to view the files and directories in the root directory that belongs to the root account.

1. **File Size**: The next number relates to the size of the files, in bytes. The `h` argument in `ls -lah` humanizes the number, making it easier to read.

1. **Hidden Files**: Be aware that hidden files in Linux are listed using the `-a` argument. Hidden files and directories begin with a dot (`.`), so you should never start a file or directory with a dot, unless you want to hide it. Typically, you can combine all three arguments into the command `ls -lah`.

### Creating and Deleting Files

Creating and deleting files is a fundamental computing skill. When using the Linux Terminal, remember that deleted files are not sent to the system recycle bin, so extra care is needed.

1. **Create a File**: Enter `cd` to move to the home directory. Type `touch testfile` and `ls -l` to view the files. You'll see a new file called `testfile` with a size of 0 because it's empty.

1. **Case Sensitivity**: Linux is case sensitive. If you enter `touch Testfile` (with a capital T), it creates a second file called `Testfile`. Enter `ls -l` to see both files. To avoid confusion, most people use lowercase letters consistently.

1. **Update Timestamp**: Enter `ls -l` and note the timestamp of `testfile`. Then enter `touch testfile` followed by `ls -l` and notice the updated time. The touch command updates files or directories with the current system time.

1. **No Spaces in File Names**: Avoid using spaces in file names. Entering `touch test file` creates two files: `test` and `file`. Instead, use an underscore (`_`), like `touch test_file`.

1. **Delete Files**: If you've followed the steps, you should have five files: `testfile`, `Testfile`, `test`, `file`, and `test_file`. To delete files, use the `rm` command. Enter `rm Testfile` to delete the file named `Testfile`. Enter `ls -l` to confirm its deletion.

1. **Use Wildcards**: Enter `ls test*` to view files that match the word `test` followed by any characters. The `*` wildcard means "any characters here." Enter `rm test*` to delete `test`, `testfile`, and `test_file`. Finally, enter `rm file` to delete it.

### Creating and Removing Directories

After learning to create files, you’ll want to know how to make directories and move items around.

1. **Create a Directory**: Enter `ls` to view directories in the home directory. Use `mkdir` to create directories. Enter `mkdir testdir` and `ls` again to see it.

1. **Timestamp Update**: Unlike touch, `mkdir` does not update the timestamp if used on an existing directory.

1. **Multiple Directories**: You can create multiple directories at once with `mkdir`. Enter `mkdir testdir2 testdir3` and `ls` to see several directories.

1. **Nested Directories**: You can create directories within directories using the directory path. Enter `mkdir Documents/photos` to create a `photos` directory inside `Documents`. The parent directory must exist, so `mkdir articles/reports` will fail if `articles` does not exist.

1. **Create Directory Path**: Use the `-p` option with `mkdir` to create a directory path. Enter `mkdir -p articles/reports` and `ls` to view the `articles` directory, and `ls articles` to see the `reports` directory inside.

1. **Remove a Directory**: Ensure you're in the home directory by entering `cd`. Then enter `ls` to view contents. Use `rmdir` to delete directories. Enter `rmdir testdir3` and `ls` to confirm deletion.

1. **Non-Empty Directories**: Try to delete the `articles` directory containing the `reports` directory. Enter `rmdir articles`. You will get an error. The `rmdir` command only removes empty directories. To delete non-empty directories, use `rm` with the `-r` (recursive) option. Enter `rm -r articles` to delete the `articles` directory containing the `reports` directory.

1. **Interactive Deletion**: Use the `-i` (interactive) option with `rm` to prompt before each deletion. Enter `rm -ri test*` and enter `Y` or `y` for each prompt. Using `-i` is a good practice with the `rm` command.


### Copying, Moving, and Renaming Files

In Linux, renaming a file is essentially moving it from one name to another, and copying a file involves moving it without deleting the original.

1. **Create Test File and Directory**: Enter `touch testfile` and `mkdir testdir` to create a test file and directory in your home directory. Enter `ls` to confirm their presence.

1. **Move Files and Directories**: Use the `mv` command with two arguments: source and destination. Enter `mv testfile testdir` to move `testfile` into `testdir`. Enter `ls` to see it’s no longer in the home directory, and `ls testdir` to see it inside `testdir`. Create a new directory with `mkdir newparent`.

1. **Move Directories**: Move directories with files using the same command. Enter `mv testdir newparent` to move `testdir` into `newparent`. Enter `cd newparent/testdir` and `ls` to see `testfile` inside `testdir`.

1. **Move Up Levels**: Use the double dot (`..`) to move up directories. Enter `ls -la` to view files, including single and double dot entries. Move `testfile` up one level with `mv testfile ..` and enter `cd ..` to move to the parent directory.

    ```{hint}
    Use the tab key to autocomplete paths for the following step.
    ```

1. **Longer Paths**: Move files using longer paths. Enter `cd ~` to return to the home directory, then `mv newparent/testfile newparent/testdir/testfile` to move `testfile` back to `testdir`. Enter `ls newparent/testdir` to confirm.

1. **Rename Files**: Rename and move a file at the same time. Enter `mv newparent/testdir/testfile newparent/testfile2`. Enter `ls newparent` to see `testfile2` in the `newparent` directory.

### Useful Commands

Linux is a vast and versatile command line language with hundreds of commands you can learn. Here are a few that can help you get more from your Ubuntu.

1. **View Processor Details**: Enter `cat /proc/cpuinfo` to see details about the processors.

1. **Using `cat`**: The `cat` command lists the contents of a text file, such as `cpuinfo`. You can also open this text file using gedit, a GUI text editor. Enter `gedit /proc/cpuinfo` to view the file in gedit. Note that `cpuinfo` is read-only.

1. **View Memory Information**: Enter `cat /proc/meminfo` to get information about your memory.

1. **Process Status**: Type `ps` to see two items: `bash` and `ps`. To view processes used by other users (including those started by root), enter `ps -a`. This option shows processes for all users but does not include background processes. For that, enter `ps -A` or `ps -e`, which shows every process on the system, including background processes. You may need to pipe it through `less` using `ps -e | less`. The `less` command allows you to view the contents one screen at a time. Press `q` to exit `less`.

1. **Real-Time Process Monitoring**: While `ps` is useful, you may need to view processes in real-time, especially to check CPU and memory usage. Use the `top` command for this.

1. **Shutdown and Restart**: To shut down the computer from the command line, enter `sudo shutdown -h now`. The `-h` option stands for "halt." To restart, enter `sudo shutdown -r` or `sudo reboot`.

### Input, Output, and Pipes

1. **Redirect Output**: Change the standard output using the `>` character after your command. For example, `ls -l /etc` lists all items in the `/etc` directory. Using `ls -l /etc > etc.txt` outputs the list to a new text file called `etc.txt`.

1. **View Output File**: The `etc.txt` file now contains the output from the `ls` command. Check it using `cat etc.txt` or `nano etc.txt`. The output from `ls -l` was sent to this file instead of the screen. Press `Ctrl+X` to quit `nano`. The `>` character allows you to output to files, but you can also get input from a file.

1. **Using Pipes**: As you advance in Linux, you create more powerful commands using the pipe character (`|`). Enter `cat ~/.bashrc` to display the `.bashrc` file's content. Now enter `cat ~/.bashrc | wc`. The output from `cat` is piped into the `wc` (word count) command, showing the number of lines, words, and characters in the document.

1. **Chaining Commands**: You can pipe commands multiple times. Enter `cat ~/.bashrc | sort | grep source*` to list lines starting with "source" in alphabetical order. The output from `cat` is passed to `sort`, and `sort`'s output is passed to `grep`, which filters out content starting with "source."


## 🚚 Deliverables

1. Visit [Git Repo Setup](../Appendix/GitSetup.md) to create a ROS workspace on the `Master` computer and configure your ECE387 classroom repository.  
1. Submit Lab 1 on Gradescope.  

<br>

**References**
<br>
1. "Raspberry Pi Tips, Tricks & Fixes Vol. 35", Edited by James Cale, BDM Limited, 2019, ISBN: 2046-2743. 































