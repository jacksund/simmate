######################################################################
#
# To call this script, make sure you have the ENV variables:
#   - HELM_ENV: prod, dev, or test
#   - HELM_NAMESPACE: simmate-ns, simmate-dev-ns, or jack-sundberg-ns 
#   - HELM_ACTION: "template" or "upgrade --install --reuse-values"
#   - HELM_VALUES_PROD: a "file" type variable that has updates for values.yaml
# These allow testing and separate deployments via our Gitlab CI.
#
######################################################################

# Print commands & exit on any errors
# https://stackoverflow.com/questions/29141436/
set -xe

# DEV NOTE: we disabled sections below because we have a local chart & that's it
#
# Register HELM repos that we will pull charts from
# helm repo add bitnami https://charts.bitnami.com/bitnami
# helm repo add runix https://helm.runix.net
#
# make sure repos are up to date
# helm repo update

# make sure the dependencies are loaded
helm dependency update envs/helm 

# make a release (or template) the chart
helm $HELM_ACTION simmate envs/helm \
-n $HELM_NAMESPACE \
-f $HELM_VALUES_PROD
