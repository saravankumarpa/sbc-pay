#!/usr/bin/env groovy
// Copyright © 2018 Province of British Columbia
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
//JENKINS DEPLOY ENVIRONMENT VARIABLES:
// - JENKINS_JAVA_OVERRIDES  -Dhudson.model.DirectoryBrowserSupport.CSP= -Duser.timezone=America/Vancouver
//   -> user.timezone : set the local timezone so logfiles report correxct time
//   -> hudson.model.DirectoryBrowserSupport.CSP : removes restrictions on CSS file load, thus html pages of test reports are displayed pretty
//   See: https://docs.openshift.com/container-platform/3.9/using_images/other_images/jenkins.html for a complete list of JENKINS env vars

import groovy.json.*

// define constants - values sent in as env vars from whatever calls this pipeline
def APP_NAME = 'report-api'
def DESTINATION_TAG = 'dev'
def TOOLS_TAG = 'tools'
def NAMESPACE_APP = 'l4ygcl'
def NAMESPACE_SHARED = 'd7eovc'
def NAMESPACE_BUILD = "${NAMESPACE_APP}"  + '-' + "${TOOLS_TAG}"
def NAMESPACE_DEPLOY = "${NAMESPACE_APP}" + '-' + "${DESTINATION_TAG}"
def NAMESPACE_UNITTEST = "${NAMESPACE_SHARED}" + '-'+ "${TOOLS_TAG}"

def ROCKETCHAT_DEVELOPER_CHANNEL='#relationship-developers'

// post a notification to rocketchat
def rocketChatNotificaiton(token, channel, comments) {
  def payload = JsonOutput.toJson([text: comments, channel: channel])
  def rocketChatUrl = "https://chat.pathfinder.gov.bc.ca/hooks/" + "${token}"

  sh(returnStdout: true,
     script: "curl -X POST -H 'Content-Type: application/json' --data \'${payload}\' ${rocketChatUrl}")
}

@NonCPS
boolean triggerBuild(String contextDirectory) {
    // Determine if code has changed within the source context directory.
    def changeLogSets = currentBuild.changeSets
    def filesChangeCnt = 0
    for (int i = 0; i < changeLogSets.size(); i++) {
        def entries = changeLogSets[i].items
        for (int j = 0; j < entries.length; j++) {
            def entry = entries[j]
            //echo "${entry.commitId} by ${entry.author} on ${new Date(entry.timestamp)}: ${entry.msg}"
            def files = new ArrayList(entry.affectedFiles)
            for (int k = 0; k < files.size(); k++) {
                def file = files[k]
                def filePath = file.path
                //echo ">> ${file.path}"
                if (filePath.contains(contextDirectory)) {
                    filesChangeCnt = 1
                    k = files.size()
                    j = entries.length
                }
            }
        }
    }

    if ( filesChangeCnt < 1 ) {
        echo('The changes do not require a build.')
        return false
    } else {
        echo('The changes require a build.')
        return true
    }
}

// Get an image's hash tag
String getImageTagHash(String imageName, String tag = "") {

    if(!tag?.trim()) {
        tag = "latest"
    }

    def istag = openshift.raw("get istag ${imageName}:${tag} -o template --template='{{.image.dockerImageReference}}'")
    return istag.out.tokenize('@')[1].trim()
}

// define job properties - keep 10 builds only
properties([[$class: 'BuildDiscarderProperty', strategy: [$class: 'LogRotator', artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '', numToKeepStr: '10']]])

def run_pipeline = true

// build wasn't triggered by changes so check with user
if( !triggerBuild(APP_NAME) ) {
    stage('No changes. Run pipeline?') {
        try {
            timeout(time: 1, unit: 'DAYS') {
                input message: "Run pipeline?", id: "1234"//, submitter: 'admin'
            }
        } catch (Exception e) {
            run_pipeline = false;
        }
    }
}

if( run_pipeline ) {
    node {
        def build_ok = true
        def old_version

        stage("Build ${APP_NAME}") {
            script {
                openshift.withCluster() {
                    openshift.withProject("${NAMESPACE_BUILD}") {
                        try {
                            echo "Building ${APP_NAME} ..."
                            def build = openshift.selector("bc", "${APP_NAME}").startBuild()
                            build.untilEach {
                                return it.object().status.phase == "Running"
                            }
                            build.logs('-f')
                        } catch (Exception e) {
                            echo e.getMessage()
                            build_ok = false
                         }
                    }
                }
            }
        }

        if (build_ok) {
            stage("Tag ${APP_NAME}:${DESTINATION_TAG}") {
                script {
                    openshift.withCluster() {
                        openshift.withProject("${NAMESPACE_DEPLOY}") {
                            old_version = openshift.selector('dc', "${APP_NAME}-${DESTINATION_TAG}").object().status.latestVersion
                        }
                    }
                    openshift.withCluster() {
                        openshift.withProject("${NAMESPACE_BUILD}") {
                            try {
                                echo "Tagging ${APP_NAME} for deployment to ${DESTINATION_TAG} ..."

                                // Don't tag with BUILD_ID so the pruner can do it's job; it won't delete tagged images.
                                // Tag the images for deployment based on the image's hash
                                def IMAGE_HASH = getImageTagHash("${APP_NAME}")
                                echo "IMAGE_HASH: ${IMAGE_HASH}"
                                openshift.tag("${APP_NAME}@${IMAGE_HASH}", "${APP_NAME}:${DESTINATION_TAG}")
                            } catch (Exception e) {
                                echo e.getMessage()
                                build_ok = false
                            }
                        }
                    }
                }
            }
        }

        if (build_ok) {
            stage("Deploy ${APP_NAME}-${DESTINATION_TAG}") {
                sleep 10
                script {
                    openshift.withCluster() {
                        openshift.withProject("${NAMESPACE_DEPLOY}") {
                            try {
                                def new_version = openshift.selector('dc', "${APP_NAME}-${DESTINATION_TAG}").object().status.latestVersion
                                if (new_version == old_version) {
                                    echo "New deployment was not triggered."
                                }

                                def pod_selector = openshift.selector('pod', [ app:"${APP_NAME}-${DESTINATION_TAG}" ])
                                pod_selector.untilEach {
                                    deployment = it.objects()[0].metadata.labels.deployment
                                    echo deployment
                                    if (deployment == "${APP_NAME}-${DESTINATION_TAG}-${new_version}" && it.objects()[0].status.phase == 'Running' && it.objects()[0].status.containerStatuses[0].ready) {
                                        return true
                                    } else {
                                        echo "Pod for new deployment not ready"
                                        sleep 5
                                        return false
                                    }
                                }
                            } catch (Exception e) {
                                echo e.getMessage()
                                build_ok = false
                            }
                        }
                    }
                }
            }
        }

        if (build_ok) {
            try {
                stage("Run tests on ${APP_NAME}:${DESTINATION_TAG}") {
                    script {
                        openshift.withCluster() {
                            openshift.withProject("${NAMESPACE_UNITTEST}") {
                                def test_pipeline = openshift.selector('bc', 'pytest-pipeline')

                                test_pipeline.startBuild('--wait=true', "-e=component=${APP_NAME}", "-e=component_tag=${DESTINATION_TAG}", "-e=tag=${DESTINATION_TAG}", "-e=namespace=${NAMESPACE_APP}", "-e=db_type=NA").logs('-f')
                                echo "All tests passed"
                            }
                        }
                    }
                }
            } catch (Exception e) {
                echo e.getMessage()
                echo "Not all tests passed."
                build_ok = false
            }
        }

        if (build_ok) {
            stage("Run E2E API tests") {

            }
        }

        stage("Notify on RocketChat") {
            if(build_ok) {
                currentBuild.result = "SUCCESS"
            } else {
                currentBuild.result = "FAILURE"
            }

            ROCKETCHAT_TOKEN = sh (
                    script: """oc get secret/apitest-secrets -n ${NAMESPACE_BUILD} -o template --template="{{.data.ROCKETCHAT_TOKEN}}" | base64 --decode""",
                        returnStdout: true).trim()

            rocketChatNotificaiton("${ROCKETCHAT_TOKEN}", "${ROCKETCHAT_DEVELOPER_CHANNEL}", "${APP_NAME} build and deploy to ${DESTINATION_TAG} ${currentBuild.result}!")
        }
    }
}

