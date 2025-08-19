# For local k8s cluster for ease of setup i chose to use Kind
# this assumes docker is already installed and you are running WSL
```
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind create cluster
kubectl cluster-info --context kind-kind
```

# run a local docker registry
```
docker run -d -p 5000:5000 --name registry registry:2
```

# make sure that kind has access to docker repo
```# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5000"]
    endpoint = ["http://host.docker.internal:5000"]
```
# create the clsuter
```
kind create cluster --name my-cluster --config kind-config.yaml
```

# move the locally built image to kinds' registry
# I already bult the image queues in task 2
```
docker tag queues localhost:5000/queues:latest
docker push localhost:5000/queues:latest
```

# manually create deployment
```
kubectl create deployment queues --image=localhost:5000/queues:latest
```
# check it is runnig

````
kubectl get pods
queues-67444d9f5c-4v86w   1/1     Running   0          15m
```

# expose node port i set it to 3000
```
kubectl expose deployment queues --type=NodePort --port=3000
```

# portforward the port so it responds on 3000
```
kubectl port-forward deployment/queues 3000:3000
```

# and in another screen terminal
```
curl http://localhost:3000

returns Hello Kube
```
# test it some more
```
curl -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -d '{
    "connect_str": "",
    "queue_name": "one-test",
    "content": {
        "priority": 3,
        "body": "From docker"
    }
}'
```
returns: {"status":"Message sent successfully"}

# set up helm
```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
# fill the values in chart, values files
# run the chart
helm install queues ./queues


# ansible and namespaces

#create namespaces to test with
kubectl create namespace dev
kubectl create namespace uat
kubectl create namespace prod

# install the chart in the default namespace
helm install queues ./queues 
kubectl port-forward svc/queues 3000:3000
# install the chart in dev
helm install queues-dev ./queues --namespace dev
kubectl port-forward svc/queues-dev -n dev 3000:3000

# debug   I had to check that the namespace var is actually being read, and after hardcoding a new text in the root path of the application i realised that the image with {{ENV}} variable is not being pulled correctly

kubectl exec -it deploy/queues -- python3 -c "import os; print(os.environ.get('NAMESPACE'))"

# so I chanhed the image pull policy to Allways in values.yaml
# now after cleaning up the hardcoded values in deployment and the pythnon code I deployed the helm chart and curling the root i get a return of
```
Hello default Kube
```
# now we can go back to testing in a named namespace:
```
helm install queues-dev ./queues --namespace dev
kubectl port-forward svc/queues-dev -n dev 3000:3000 # in a separate terminal

# quick curl
bazilbrush@DESKTOP-CNKLI1P:/mnt/d/Programming/github/test-tasks-tf-ansible/task3$ curl http://localhost:3000
Hello dev Kubebazilbrush@DESKTOP-CNKLI1P:/mnt/d/Programming/github/test-tasks-tf-ansible/task3$

```
# ansible time
# we need to install helm library

ansible-galaxy collection install community.kubernetes kubernetes.core

we need these libararies to talk to local cluster 
python3 -m pip install openshift pyyaml kubernetes

# first run the playbook with just the task to check namespaces exist to see if it's talking to the clsuter
```
- name: Deploy queues app to Kubernetes
  hosts: all
  gather_facts: no
  vars:
    helm_chart_path: ./queues   
    release_name: queues
  tasks:
    - name: Ensure namespace exists
      kubernetes.core.k8s:
        api_version: v1
        kind: Namespace
        name: "{{ namespace }}"
        state: present

```
# run the full playbook against the dev host and port forward to test the app works
in ansible directory:
ansible-playbook -i inventory.yml playbook.yml

TASK [Deploy Helm chart] *****************
changed: [devhost]
# in a separate terminal
kubectl port-forward svc/queues-dev -n dev 3000:3000 

# for the purposes of demonstration i added a few plays that deploy and clean up to one or more environments, as well as a play that would simulate a playbook failure. 

# What could have been done better:
1. run this against a proper k8s cluster, i'm sure there will be extra issues that could come up.
2. work out a robust image pull policy, that can help with zero downtime deployments
3. cleaner helm chart (im sure i have a lot to learn on that part)
4. Playbook design:
      - playbooks ideally should be handled by a pipeline that would help with the promotion strategy through dev>uat>prod
        where at every stage there are quality gates that would halt deployment and rollback to last known stable state
      - usage of roles: i know this playbook is very barebones and uses only 3 tasks, but in a production scenario there will be spcific cases where more things will need to be handled
      - inventory: right now it's static, depending on what is required it can be templated via the pipelines so the variables inside like imagetag can be updated on a new software release
        or it can be dynamic for example if the pipeline is building a cluster via terraform and then hands over control of the hosts to ansible

