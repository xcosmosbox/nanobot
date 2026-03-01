
## 📦 Install

Git clone 

```bash
git clone https://github.com/xcosmosbox/nanobot.git
cd nanobot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

> We use the command `pip install -e .` to install the nanobot package as a local module, which allows us to use the `nanobot` command in the terminal.

## 🚀 Quick Start

> [!TIP]
> Set your API key in `~/.nanobot/config.json`.

**1. Initialize nanobot config**

```bash
nanobot onboard
```

> This command will create and initialize the file `~/.nanobot/config.json`.

**2. Configure** (`~/.nanobot/config.json`)

Add or merge these **two parts** into your config (other options have defaults).

*Set your API key* 

```json
{
  "providers": {
    "<YOU_SELECTED_PROVIDERS>": {
      "apiKey": "<YOUR_API_KEY>"
    }
  }
}
```

*Set your model* 

```json
{
  "agents": {
    "defaults": {
      "model": "<MODEL_NAME>",
      "provider": "<PROVIDER_NAME>"
    }
  }
}
```

> [!IMPORTANT]
>
> To successfully complete the experimental comparison, we need at least two models and providers. In my experiments, I used Minimax and DeepSeek.

Before each experiment, we need to manually change the model used by our default agent. Like this:

![image-20260301190536249](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301190536249.png)

![image-20260301190604988](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301190604988.png)

> [!NOTE]
>
> To ensure the experiment runs properly, we need to modify the default value of `maxToolIterations` (which is 40), as our task is relatively complex and the default value of `maxToolIterations` is insufficient for our needs.



## 💬 Chat Apps

Connect nanobot to Telegram, we must be to get the bot token from @BotFather

| Channel | What you need |
|---------|---------------|
| **Telegram** | Bot token from @BotFather |

<details>
<summary><b>Telegram</b></summary>

**1. Create a bot**

- Open Telegram, search `@BotFather`
- Send `/newbot`, follow prompts
  - ![image-20260301185754527](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301185754527.png)
  - ![image-20260301185841044](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301185841044.png)

- Copy the bot token to your config file

**2. Configure**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": [] #empty means all user could call your bot includs yourself 
    }
  }
}
```

**3. Run**

```bash
nanobot gateway
```

> Use this command to officially launch nanobot and listen for messages from Telegram.

![image-20260301190853096](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301190853096.png)

You must have at least one conversation in Telegram to allow subsequent tests to run properly.

After you have run one conversation, you may use **Ctrl+C** to force quit nanobot, and we will start the main experimental process.



## Experimental Process

### 1.Create a separate worktree

Use the command `git worktree add -b <your-branch-name> <worktree-path> main` to create a separate worktree.

Since we have two agents, we need to create **two** worktrees for the comparative experiment.

Such as:

 `git worktree add -b minimax .worktree/minimax main` 

 `git worktree add -b deepseek .worktree/deepseek main` 

These two commands will create two separate branches for us from the main branch, named `minimax` and `deepseek` respectively, and the worktree code they track will be located at `.worktree/minimax` and `.worktree/deepseek` respectively.

### 2.Modify the task prompt

Modify the descriptions of `worktree` in `.worktree/minimax/task_prompt.txt` and `.worktree/deepseek/task_prompt.txt` respectively, pointing them to the regions they should encode.

![image-20260301193827603](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301193827603.png)

![image-20260301193850630](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301193850630.png)

### 3.Start the experiment

We go to different project directories in sequence to start the tests.

> Experiment 1 -> minimax

Modify config file to change to minimax model.

![image-20260301190536249](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301190536249.png)



```bash
source .venv/bin/activate    # run this code on project root path

cd .worktree/minimax         # go to minimax codespace

touch log.txt                # create log file to store agent output

/usr/bin/time -p nanobot agent --logs --no-markdown -s minimax -m "$(cat task_prompt.txt)" | tee logs.txt               # Use the system's time utility to measure the elapsed time, then launch nanobot from the virtual environment in the project's root directory, and set it to logs mode with no-markdown format. In logs mode, the agent will output human-readable content, which will be summarized into logs.txt. The -s parameter is used to select a custom-named session (here it is minimax); if this session does not exist, the agent will create it. The -m parameter specifies the prompt we input to the model, and we will feed the entire content of task_prompt.txt to the agent.

#########################      Wait for the task to complete.      #######################
```

Once the task is completed, we will obtain a log file and a session file. The log file is used to summarize the agent’s behavior and output, while the session file can be used to count tool calls.

The session is stored in the `~/.nanobot/sessions` directory.

> Experiment 2 -> deepseek

Modify config file to change to deepseek model.

![image-20260301190604988](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301190604988.png)

```bash
source .venv/bin/activate    # run this code on project root path

cd .worktree/deepseek         # go to minimax codespace

touch log.txt                # create log file to store agent output

/usr/bin/time -p nanobot agent --logs --no-markdown -s deepseek -m "$(cat task_prompt.txt)" | tee logs.txt               # Use the system's time utility to measure the elapsed time, then launch nanobot from the virtual environment in the project's root directory, and set it to logs mode with no-markdown format. In logs mode, the agent will output human-readable content, which will be summarized into logs.txt. The -s parameter is used to select a custom-named session (here it is deepseek); if this session does not exist, the agent will create it. The -m parameter specifies the prompt we input to the model, and we will feed the entire content of task_prompt.txt to the agent.

#########################      Wait for the task to complete.      #######################
```

Once the task is completed, we will obtain a log file and a session file. The log file is used to summarize the agent’s behavior and output, while the session file can be used to count tool calls.

The session is stored in the `~/.nanobot/sessions` directory.

### 4.Manual verification

Based on the task requirements, if the agent is successfully developed and completed, we need to add the field `screenshot:enabled` in the config file to enable this function (this is also part of the function verification)

![image-20260301222551374](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301222551374.png)

We must navigate to the different worktrees and create separate Python virtual environments for each, as our goal is to package the nanobot of each worktree within that worktree itself, to verify that the new functions can run properly.

`.worktree/minimax` :

```bash
cd .worktree/minimax                # go to codespace
python3 -m venv .minimax_venv       # create python runtime envriment
source .minimax_venv/bin/activate   # choose minimax_venv as runtime envriemnt
python -m pip install -e .          # package minimax codespace as nanobot module
nanobot gateway                     # start nanobot 
```

Now we need to go to Telegram and send "**Take a screenshot of the desktop, then send the screenshot image to me**." to get a reply from the agent.

![image-20260301215736656](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301215736656.png)

`.worktree/deepseek` :

```bash
cd .worktree/deepseek               # go to codespace
python3 -m venv .deepseek_venv       # create python runtime envriment
source .deepseek_venv/bin/activate   # choose deepseek_venv as runtime envriemnt
python -m pip install -e .          # package deepseek codespace as nanobot module
nanobot gateway                     # start nanobot 
```

Now we need to go to Telegram and send "**Take a screenshot of the desktop, then send the screenshot image to me**." to get a reply from the agent.

![image-20260301215744592](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301215744592.png)

### 5.Summary

Go to this free website: https://www.merge-json-files.com/#tools

![image-20260301220122366](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301220122366.png)

To convert JSONL to JSON for session files.

We can count the number of calls for various tools in it.

![image-20260301220206962](/Users/yuxiangfeng/Library/Application Support/typora-user-images/image-20260301220206962.png)



## Reference

Config file: `~/.nanobot/config.json`

### Providers

> [!TIP]
> - **Groq** provides free voice transcription via Whisper. If configured, Telegram voice messages will be automatically transcribed.
> - **Zhipu Coding Plan**: If you're on Zhipu's coding plan, set `"apiBase": "https://open.bigmodel.cn/api/coding/paas/v4"` in your zhipu provider config.
> - **MiniMax (Mainland China)**: If your API key is from MiniMax's mainland China platform (minimaxi.com), set `"apiBase": "https://api.minimaxi.com/v1"` in your minimax provider config.
> - **VolcEngine Coding Plan**: If you're on VolcEngine's coding plan, set `"apiBase": "https://ark.cn-beijing.volces.com/api/coding/v3"` in your volcengine provider config.

| Provider | Purpose | Get API Key |
|----------|---------|-------------|
| `custom` | Any OpenAI-compatible endpoint (direct, no LiteLLM) | — |
| `openrouter` | LLM (recommended, access to all models) | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | LLM (Claude direct) | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | LLM (GPT direct) | [platform.openai.com](https://platform.openai.com) |
| `deepseek` | LLM (DeepSeek direct) | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | LLM + **Voice transcription** (Whisper) | [console.groq.com](https://console.groq.com) |
| `gemini` | LLM (Gemini direct) | [aistudio.google.com](https://aistudio.google.com) |
| `minimax` | LLM (MiniMax direct) | [platform.minimaxi.com](https://platform.minimaxi.com) |
| `aihubmix` | LLM (API gateway, access to all models) | [aihubmix.com](https://aihubmix.com) |
| `siliconflow` | LLM (SiliconFlow/硅基流动) | [siliconflow.cn](https://siliconflow.cn) |
| `volcengine` | LLM (VolcEngine/火山引擎) | [volcengine.com](https://www.volcengine.com) |
| `dashscope` | LLM (Qwen) | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `moonshot` | LLM (Moonshot/Kimi) | [platform.moonshot.cn](https://platform.moonshot.cn) |
| `zhipu` | LLM (Zhipu GLM) | [open.bigmodel.cn](https://open.bigmodel.cn) |
| `vllm` | LLM (local, any OpenAI-compatible server) | — |
| `openai_codex` | LLM (Codex, OAuth) | `nanobot provider login openai-codex` |
| `github_copilot` | LLM (GitHub Copilot, OAuth) | `nanobot provider login github-copilot` |


## CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config & workspace |
| `nanobot agent -m "..."` | Chat with the agent |
| `nanobot agent` | Interactive chat mode |
| `nanobot agent --no-markdown` | Show plain-text replies |
| `nanobot agent --logs` | Show runtime logs during chat |
| `nanobot gateway` | Start the gateway |
| `nanobot status` | Show status |
| `nanobot provider login openai-codex` | OAuth login for providers |
| `nanobot channels login` | Link WhatsApp (scan QR) |
| `nanobot channels status` | Show channel status |

Interactive mode exits: `exit`, `quit`, `/exit`, `/quit`, `:q`, or `Ctrl+D`.







