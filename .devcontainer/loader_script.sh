#!/bin/bash
# set -e  # Commented out to allow script to continue on errors
source .env  # Load environment variables

curl -sS https://raw.githubusercontent.com/diogocavilha/fancy-git/master/install.sh | sh
cp /tmp/app_config ~/.fancy-git/app_config
git config --global credential.helper store
git config --global credential.interactive auto
git config --global credential.useHttpPath true
git config --global user.email $USERNAME@police.tas.gov.au
git config --global user.name $USERNAME
git config --global --add safe.directory $(pwd)
git config --global http.proxy http://proxy.police.tas.gov.au:8080
git config --global https.proxy http://proxy.police.tas.gov.au:8080
git config --global http.noProxy localhost,127.0.0.1,.local  # Added line to bypass proxy for local addresses


SSH_CONFIG="$HOME/.ssh/config"
HOST_TO_CHECK="ssh.dev.azure.com"
echo "---------------------------------------------------------------------"
echo "START - write_ssh_config"
# Function to write SSH config
write_ssh_config() {
    echo "Host $HOST_TO_CHECK" >> "$SSH_CONFIG"
    echo "    IdentityFile ~/.ssh/id_rsa" >> "$SSH_CONFIG"
    echo "    IdentitiesOnly yes" >> "$SSH_CONFIG"
    echo "    HostkeyAlgorithms +ssh-rsa" >> "$SSH_CONFIG"
    echo "    PubkeyAcceptedKeyTypes=ssh-rsa" >> "$SSH_CONFIG"
    echo "    ProxyCommand corkscrew inthaproxy.ems.tas.gov.au 8080 %h %p" >> "$SSH_CONFIG"
}

# Create SSH config directory if it doesn't exist
#mkdir -p "$HOME/.ssh"

# If config file doesn't exist, create it and write config
if [ ! -e "$SSH_CONFIG" ]; then
    write_ssh_config
else
    # Check if Host entry exists
    if ! grep -q "^Host $HOST_TO_CHECK\$" "$SSH_CONFIG"; then
        write_ssh_config
    fi
fi
# Set appropriate permissions
#chmod 700 "$SSH_CONFIG"

# Add SSH agent management with session persistence to avoid repeated authentication
cat >> ~/.bashrc << 'EOF'

# SSH Agent management - only start if not already running
if [ -z "$SSH_AUTH_SOCK" ] || [ ! -S "$SSH_AUTH_SOCK" ]; then
    # Check if there's already an agent running
    if [ -f ~/.ssh/agent-environment ]; then
        source ~/.ssh/agent-environment > /dev/null
    fi

    # Test if the agent is still valid
    if ! ssh-add -l > /dev/null 2>&1; then
        # Start new agent and save environment
        eval "$(ssh-agent -s)" > /dev/null
        echo "export SSH_AUTH_SOCK=$SSH_AUTH_SOCK" > ~/.ssh/agent-environment
        echo "export SSH_AGENT_PID=$SSH_AGENT_PID" >> ~/.ssh/agent-environment

        # Only add key if it exists and is not already loaded
        if [ -f ~/.ssh/id_rsa ] && ! ssh-add -l | grep -q ~/.ssh/id_rsa; then
            ssh-add ~/.ssh/id_rsa 2>/dev/null || true
        fi
    fi
fi
EOF
echo "END -  write_ssh_config"
echo "---------------------------------------------------------------------"
echo "---------------------------------------------------------------------"
echo "START - Add useful aliases"
echo "alias ll='ls -l'" >> ~/.bashrc
echo "alias la='ls -A'" >> ~/.bashrc
echo "alias l='ls -CF'" >> ~/.bashrc
echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc

ln -sf ~/.claude $(pwd)/.claude
ln -sf ~/.claude.json $(pwd)/.claude.json

mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "END - Add useful aliases"
echo "---------------------------------------------------------------------"
echo "---------------------------------------------------------------------"
# echo "CHMOD"
# #chmod +x $(pwd)/.devcontainer/add_requirements_to_uv.sh
# chmod +x $(pwd)/.devcontainer/start_mcp_servers.sh
# echo "---------------------------------------------------------------------"
# # echo "add_requirements_to_uv"
# # uv --no-project sync
# #. $(pwd)/.devcontainer/add_requirements_to_uv.sh $(pwd)/.devcontainer/requirements.txt
# echo "---------------------------------------------------------------------"
echo "add mcp servers to claude"
# claude mcp add ado -e AZURE_DEVOPS_PAT=$AZURE_DEVOPS_PAT -e AZURE_DEVOPS_PROJECT="$AZURE_DEVOPS_PROJECT" -- npx -y @azure-devops/mcp emstas
# claude mcp add --transport http Ref https://api.ref.tools/mcp\?apiKey\=ref-40e54e07e3ea2a7f36b9
# claude mcp add exa -e EXA_API_KEY=e72b1a0c-0764-41bc-b2ba-5647cb81d582 -- npx -y exa-mcp-server
# echo "---------------------------------------------------------------------"
# echo "START - bmad-method install"
# npx bmad-method install
# echo "END - bmad-method install"
# echo "---------------------------------------------------------------------"
# Load LinkedIn cookie from .env file in project root
if [ -f "$(pwd)/.env" ]; then
    source "$(pwd)/.env"
    if [ -n "$LINKEDIN_COOKIE" ]; then
        echo "Starting LinkedIn MCP Server with cookie from .env..."
        uvx --from git+https://github.com/stickerdaniel/linkedin-mcp-server linkedin-mcp-server --cookie "$LINKEDIN_COOKIE"
    else
        echo "Warning: LINKEDIN_COOKIE not found in .env file"
    fi
else
    echo "Warning: .env file not found at $(pwd)/.env"
fi
