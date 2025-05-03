# Task on planning in PDDL

Planner: http://www.fast-downward.org/

Original task is fairytale-ish in Czech, I translated the code to English, but not the task itself.

```shell
$ git clone https://github.com/aibasel/downward.git
$ ./downward/build.py # requires cmake, python etc
$ ./downward/fast-downward.py en/domain.pddl en/problem.pddl --search "astar(lmcut())"
$ # or
$ ./downward/fast-downward.py en/domain.pddl en/problem.pddl --search "astar(impdb())"
```

Then take a look on planner produced `sas_plan` file.
