# Chainlit Claude AIアシスタント

ChainlitフレームワークとClaude APIを使用したAIアシスタントアプリケーションです。
Model Control Protocol (MCP)をサポートし、外部ツールとの統合が可能です。

## セットアップ

### 1. Python仮想環境の作成

```bash
python -m venv venv
```

### 2. 仮想環境の有効化

**Windows (PowerShell):**
```bash
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
.\venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルを作成し、以下の情報を設定してください:

```bash
# Claude API Key
ANTHROPIC_API_KEY=your-api-key-here

# CData MCP Server Configuration (オプション)
CDATA_MCP_URL=https://mcp.cloud.cdata.com/mcp/
CDATA_MCP_USERNAME=your-email@example.com
CDATA_MCP_API_KEY=your-cdata-api-key
```

## 実行方法

```bash
chainlit run app.py -w
```

`-w`オプションは、ファイルの変更を監視して自動的に再読み込みします。

ブラウザで `http://localhost:8000` にアクセスしてアプリケーションを使用できます。

## MCP (Model Control Protocol) の使用方法

### MCP接続の追加

1. アプリケーションを起動後、右上のメニューから「MCP Connections」を選択
2. 「Add Connection」をクリック
3. 接続情報を入力:
   - **Connection Name**: 任意の名前（例: `cdata-tools`）
   - **Type**: `sse` または `streamable-http` を選択
   - **URL**: CData MCP サーバーのURL（例: `https://mcp.cloud.cdata.com/mcp/`）
   - **Headers**: 認証情報を追加
     ```json
     {
       "X-Username": "your-email@example.com",
       "X-API-Key": "your-cdata-api-key"
     }
     ```

### 使用例

MCP接続を追加すると、Claudeは自動的に利用可能なツールを認識します。

例えば、CData MCPサーバーに接続している場合:

```
ユーザー: "Salesforceのアカウント情報を取得してください"
Claude: [CData MCPツールを使用してSalesforceにアクセス]
```

## 機能

- ✅ Claude AIとのリアルタイムチャット
- ✅ ストリーミングレスポンス
- ✅ 会話履歴の保持
- ✅ MCP (Model Control Protocol) サポート
- ✅ 外部ツールとの統合
- ✅ ツール呼び出しの可視化
- ✅ 日本語対応

## 使用技術

- **Chainlit**: チャットUIフレームワーク
- **Anthropic Claude API**: AI言語モデル
- **MCP (Model Control Protocol)**: ツールプロバイダー統合
- **Python-dotenv**: 環境変数管理

## トラブルシューティング

### MCP接続エラー

- URLが正しいか確認してください
- 認証情報（Username、API Key）が正しいか確認してください
- ネットワーク接続を確認してください

### ツールが表示されない

- MCP接続が正常に確立されているか確認してください
- ブラウザのコンソールでエラーメッセージを確認してください
