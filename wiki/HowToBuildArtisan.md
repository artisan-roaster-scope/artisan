# How to build Artisan install packages from source on GitHub.  

____
**Important: Artisan is licensed under [The GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.html).  Copies of Artisan and derivative works are subject to this license.  Be sure to review the license to understand your legal obligations and please respect them.**  
____

### Introduction

Artisan official and continuous install packages for **Windows**, **macOS** and **Linux** are built from the GitHub repository using [AppVeyor CI/CD](https://www.appveyor.com).  This is an automated process, known as continuous integration (CI), that begins whenever a commit is made to the GitHub repository.  All the necessary files to manage the CI process are contained in the [Artisan GitHub repository](https://github.com/artisan-roaster-scope/artisan).  

Users may [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) the Artisan repository to their own GitHub account and then build Artisan install packages using their own AppVeyor account.

Since Artisan is officially built and packaged on AppVeyor, the process works straight out of the box using the files in the Artisan repository.  Follow the instructions below. 

While this document is presumed free of errors as of July 2023, there is no guarantee that is is correct as you read it.  If you find an error or discrepancy please start a [new general discussion](https://github.com/artisan-roaster-scope/artisan/discussions/new?category=general) on GitHub.

*Note: Building Artisan install packages on a local machine cannot be done without modifying the repository files. The Artisan team does not have the resources to support users making local builds.*

### What Happens

Whenever a commit is made to the repository a number of actions occur. On GitHub several scripts are executed to, among other things, 
  * validate and correct certain possible inconsistencies in the committed files,  
  * validate Python code with several linting tools,  
  * trigger the CI process on AppVeyor causing the build and deployment (CD) of the packages back to GitHub.


### Step by Step

#### Setup Accounts  
1. [Sign up](https://github.com/signup) to create a GitHub account if you do not already have one.
1. [Login](https://github.com/login) to your GitHub account.
1. [Fork the Artisan repository](https://github.com/artisan-roaster-scope/artisan/fork) to your GitHub account.
1. [Create](https://ci.appveyor.com/signup) an account on AppVeyor.  There are multiple ways to create an account, it is recommended to select the plan "FREE - for open-source projects" then click the GitHub button.  A confirmation window will open.  Click **Authorize AppVeyor**.
1. Click **NEW PROJECT**.  On the next page click **Authorize GitHub** under "Authorize as OAuth App".  Click **Authorize AppVeyor** in the confirmation page that opens.  
1. Appveyor should now ask "Select repository for your new project".  Click on the repository created earlier by the fork.
1. This completes the setup required to build installation packages on AppVeyor.

#### Start a CI Build.
Make a commit to your GitHub repository.  If working ina locl clone do not forget to push the commit.  This will trigger the GitHub actions listed above including starting the CI build.    

If you encounter this message on AppVeyor: *"There was an error while trying to complete the current operation. Please contact AppVeyor support."* you must send an email to support@appveyor.com asking to have your account enabled.

**Happy Building**

_____
###### Expert Level Notes
Normally this is not required, however it is possible to connect to the build image on AppVeyor during CI.  The code to open a connection will be found in the *on_finish* section for each platform in `.appveyor.yml`.  Before connections can be made, environment variables must be added to the AppVeyor project settings or directly in `.appveyor.yml` as descibed here for  [Windows](https://www.appveyor.com/docs/how-to/rdp-to-build-worker/) or [Linux](https://www.appveyor.com/docs/how-to/ssh-to-build-worker/)  or [macOS](https://www.appveyor.com/docs/how-to/vnc-to-build-worker/).  You must watch the AppVeyor build log.  The IP and port information will be shown there when the connection is opened.  Appveyor creates a file that needs to be deleted to allow the CI process to continue.  Total CI time is currently limited to 60 min.  The connection will close and the CI build terminated when time expires.
