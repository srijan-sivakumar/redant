# Code Considerations

On going through the [test_runner](../core/test_runner.py) or [runner_thread](../core/runner_thread.py), one might think as to why did we use the a list to store a single value in the `testStats[testResult]` variable?
The reason for doing so is based on how python works and the mutable nature of list object in python. Since, we don't have pointers in python we use the mutable nature of lists to modify the values of list by reference and use it across the functions. For reference, one can checkout this article on [pointers-in-python](https://unix.stackexchange.com/questions/321697/why-is-looping-over-finds-output-bad-practice)
