# pecos-toolkit




## Description
This project is a toolkit developed for PECOS based quantum circuit simulations of quantum error correction codes (QECCs). Currently, this project implements:

+ (WIP) A Fault Tolerant Steane code up to circuit noise.

The toolkit implements a few changes to the standard pecos QuantumCircuit, extending its features. It also offers a highly customizable error generator and a circuit runner with extended features. The repository aims to be an object oriented implementation which is in line with PECOS.

If desired, with a little tweaking, the error generator could be integrated into standard PECOS.


## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Dependencies
This package depends on the internal PECOS version provided by Sascha Heußen. Currently there is no repository for this version.

## Installation
To install this package follow these steps:

+ Download or clone this repository
+ Open the project root directory
+ (Make sure to activate your virtual environment where PECOS is installed if you are using one)
+ run `pip install .` for a regular install or `pip install . -e` in dev mode. The second command will ensure that you can keep developing the package without having to reinstall it.

## Getting Started
TODO: this section will be amended at some later point in time. For questions on how to use this toolkit, please contact me.

## Usage
TODO: this section will be amended at some later point in time. Currently, scripts using this toolkit are NOT included in this repository.

## Support
For support please contact me on mattermost or email me at [luc.kusters@rwth-aachen.de](mailto:luc.kusters@rwth-aachen.de)

## Future goals
+ [] Add surface code

## Authors and acknowledgment
+ Luc Kusters

## License
This project is licensed under the gnu general public license v3

## Project status
This project is currently under development as part of my masters' thesis.

***

## TODOs

### Integrate tools

- [ ] [Set up project integrations](https://git.rwth-aachen.de/masters-thesis/code/pecos-toolkit/-/settings/integrations)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing(SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Getting Started
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.
