#!/bin/bash
jq --version >/dev/null 2>&1 || { echo >&2 "I require jq but it's not installed.  Aborting."; exit 1; }
### Please edit grafana_* variables to match your Grafana setup:
grafana_host="http://localhost:3000"
grafana_cred="admin:admin"
# Keep grafana_folder empty for adding the dashboards in "General" folder
grafana_folder="AWS CloudWatch"
ds=(1516 677 139 674 590 659 758 623 617 551 653 969 650 644 607 593 707 575 1519 581 584 2969 8050 11099 11154 11155 12979 13018 13040 13104 13892);
folderId=$(curl -s -k -u "$grafana_cred" $grafana_host/api/folders | jq -r --arg grafana_folder  "$grafana_folder" '.[] | select(.title==$grafana_folder).id')
if [ -z "$folderId" ] ; then echo "Didn't get folderId" ; else echo "Got folderId $folderId" ; fi
for d in "${ds[@]}"; do
  echo -n "Processing $d: "
  j=$(curl -s -k -u "$grafana_cred" $grafana_host/api/gnet/dashboards/$d | jq .json)
  payload="{\"dashboard\":$j,\"overwrite\":true"
  if [ ! -z "$folderId" ] ; then payload="${payload}, \"folderId\": $folderId }";  else payload="${payload} }" ; fi
  curl -s -k -u "$grafana_cred" -XPOST -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    $grafana_host/api/dashboards/import; echo ""
done
