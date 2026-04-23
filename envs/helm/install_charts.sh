set -xe
helm dependency update envs/helm 
helm $HELM_ACTION simmate envs/helm \
-n $HELM_NAMESPACE \
-f $HELM_VALUES_PROD
