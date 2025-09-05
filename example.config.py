collectorTag = "nht-collector-01"

clients = []

# Copy template and append statement for each client and modify with relevant client credentials

template = {
    "name": "clientName",
    "nsxLabels": ["label1", "label2"],
    "workspaceID": "123",
    "workspaceKey": "abc",
}

clients.append(template)
