# 🙋 FAQ

(faq-general)=
## General

### _/usr/bin/env: ‘python3\r’: No such file or directory_

```bash
$ ros2 run lab1 mouse_client.py
/usr/bin/env: ‘python3\r’: No such file or directory
```

The problem is your line ending characters. Your file was created or edited on a Windows system and uses Windows/DOS-style line endings (CR+LF), whereas Linux systems like Ubuntu require Unix-style line endings (LF).

- Sublime: Open the desired file with Sublime and from the top menu select View -> Line Endings and then the Windows(CRLF) or Unix(LF). That’s it.
- VS Code: At the bottom right of the screen in VS Code there is a little button that says `LF` or `CRLF`: Click that button and change it to your preference.

<br>


### Gazebo Error

If you have an error when you run the following command

```bash
ros2 launch turtlebot3_gazebo empty_world.launch.py
```
<br>

The error message looks like:

```
[gzclient-2] gzclient: /usr/include/boost/smart_ptr/shared_ptr.hpp:728: typename boost::detail::sp_member_access<T>::type boost::shared_ptr<T>::operator->() const [with T = gazebo::rendering::Camera; typename boost::detail::sp_member_access<T>::type = gazebo::rendering::Camera*]: Assertion `px != 0' failed.
[ERROR] [gzclient-2]: process has died [pid 7768, exit code -6, cmd 'gzclient'].
```

Then, the solution is to source Gazebo's setup file, i.e.:

```bash
. /usr/share/gazebo/setup.sh
```

This is needed to set some necessary environment variables in case they're going to be overridden, which is a common use case. 

### How to check if a package is installed

If we would like to check if `turtlesim` is installed, run

```bash
ros2 pkg executables turtlesim
```



### _ERROR: cannot launch node of type_

```
[robot98-0]: ERROR: cannot launch node of type [lab4/stop_detector.py]: lab4
ROS path [0]=/opt/ros/noetic/share/ros
ROS path [1]=/opt/ros/noetic/share
```

Ensure you have the `env-loader` field in the `machine` block of the lauch file.
```
    <machine
      name="robot0"
      address="robot0"
      env-loader="/home/pi/robot_ws/devel/remote_env_loader.sh"
      default="true"
      user="pi"
    />
```


### Why is removing elements from a list while interating over it a bad idea?


Removing elements from a list while iterating over it can lead to unexpected behavior, such as skipping elements or causing an index error. This happens because modifying the list changes its size and shifts the remaining elements, leading to incorrect indexing.  

### Example of Unexpected Behavior:  
```python
numbers = [1, 2, 3, 4, 5]

for num in numbers:
    if num % 2 == 0:
        numbers.remove(num)

print(numbers)  # Output: [1, 3, 5]
```
#### Why is this wrong?  
- The loop skips `4` because when `2` is removed, the list shifts left, and the next element (`3`) takes its place.  
- Since the loop moves to the next index (`3`), it **skips checking `4`**, which remains in the list.  

### Correct Approaches:  

#### 1. Iterate Over a Copy:  
```python
numbers = [1, 2, 3, 4, 5]

for num in numbers[:]:  # Iterate over a copy of the list
    if num % 2 == 0:
        numbers.remove(num)

print(numbers)  # Output: [1, 3, 5]
```
Using `numbers[:]` creates a **copy**, so the original list is modified safely.  

#### 2. Use List Comprehension (Best for Simplicity):  
```python
numbers = [1, 2, 3, 4, 5]
numbers = [num for num in numbers if num % 2 != 0]  # Keep only odd numbers
print(numbers)  # Output: [1, 3, 5]
```
List comprehension efficiently **creates a new filtered list** without modifying the original list during iteration.  

#### 3. Use `filter()` (Functional Approach):  
```python
numbers = [1, 2, 3, 4, 5]
numbers = list(filter(lambda x: x % 2 != 0, numbers))
print(numbers)  # Output: [1, 3, 5]
```
The `filter()` function applies a condition and constructs a new list while avoiding in-place modification issues.  

Would you like an example related to ROS2 or another specific case?