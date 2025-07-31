#!/bin/bash

# ⚡ Quick Setup & Development Tools

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

# 開発環境クイックセットアップ
quick_setup() {
    log_info "⚡ Multi-Agent 開発環境クイックセットアップ"
    echo ""
    
    # 必要なディレクトリ確保
    mkdir -p logs tmp results scripts
    
    # tmux設定適用
    if [ -f ".tmux.conf" ]; then
        log_info "tmux設定を適用中..."
        tmux source-file .tmux.conf 2>/dev/null || log_info "tmux未起動のため後で適用されます"
    fi
    
    # エージェント送信スクリプトを実行可能にする
    chmod +x agent-send.sh
    chmod +x setup.sh
    
    # 監視ツールを実行可能にする
    chmod +x scripts/monitor.sh
    
    log_success "クイックセットアップ完了"
}

# Claude Code一括起動
start_all_claude() {
    log_info "🚀 Claude Code エージェント一括起動"
    
    # presidentセッション確認・起動
    if tmux has-session -t president 2>/dev/null; then
        log_info "president セッションでClaude Code起動中..."
        tmux send-keys -t president 'npx claude --dangerously-skip-permissions' C-m
    else
        log_info "president セッションが見つかりません"
    fi
    
    # multiagentセッション確認・起動
    if tmux has-session -t multiagent 2>/dev/null; then
        log_info "multiagent セッションでClaude Code一括起動中..."
        for i in {0..3}; do
            tmux send-keys -t multiagent:agents.$i 'npx claude --dangerously-skip-permissions' C-m
            sleep 1
        done
    else
        log_info "multiagent セッションが見つかりません"
    fi
    
    log_success "Claude Code一括起動完了"
}

# 開発セッション開始
start_dev_session() {
    log_info "💻 開発セッション開始"
    
    # 環境セットアップ
    ./setup.sh
    
    # Claude Code起動
    start_all_claude
    
    # 監視ツール起動（バックグラウンド）
    log_info "監視ツールを起動中..."
    echo ""
    
    log_success "開発セッション準備完了！"
    echo ""
    echo "📋 次のステップ:"
    echo "  1. tmux attach-session -t president    # PRESIDENT画面"
    echo "  2. tmux attach-session -t multiagent   # マルチエージェント画面"
    echo "  3. ./scripts/monitor.sh                # システム監視"
    echo "  4. PRESIDENTに「あなたはpresidentです。指示書に従って」と入力"
}

# システム状態チェック
status_check() {
    log_info "🔍 システム状態チェック"
    echo ""
    
    # Tmuxセッション確認
    echo "📺 Tmux Sessions:"
    tmux list-sessions 2>/dev/null || echo "  なし"
    echo ""
    
    # エージェント状態
    echo "🤖 Agent Status:"
    ./agent-send.sh --list
    echo ""
    
    # 最新ログ
    echo "📝 Recent Activity:"
    if [ -f "./logs/send_log.txt" ]; then
        tail -3 ./logs/send_log.txt
    else
        echo "  ログなし"
    fi
}

# 全システムリセット
reset_all() {
    log_info "🔄 システム全体リセット"
    
    # tmuxセッション終了
    tmux kill-session -t multiagent 2>/dev/null || true
    tmux kill-session -t president 2>/dev/null || true
    
    # 作業ファイル削除
    rm -f ./tmp/*.txt 2>/dev/null || true
    
    # ログクリア（直近のみ残す）
    if [ -f "./logs/send_log.txt" ]; then
        tail -50 ./logs/send_log.txt > ./logs/send_log_backup.txt
        mv ./logs/send_log_backup.txt ./logs/send_log.txt
    fi
    
    log_success "システムリセット完了"
}

# メイン処理
main() {
    case "${1:-help}" in
        "setup"|"s")
            quick_setup
            ;;
        "start"|"dev")
            start_dev_session
            ;;
        "claude"|"c")
            start_all_claude
            ;;
        "status"|"st")
            status_check
            ;;
        "reset"|"r")
            reset_all
            ;;
        "help"|"h"|"--help")
            echo "🛠️  Multi-Agent 開発ツール"
            echo "========================"
            echo ""
            echo "使用方法:"
            echo "  $0 [setup|s]    - 環境クイックセットアップ"
            echo "  $0 [start|dev]  - 開発セッション開始"
            echo "  $0 [claude|c]   - Claude Code一括起動"
            echo "  $0 [status|st]  - システム状態確認"
            echo "  $0 [reset|r]    - システム全体リセット"
            echo "  $0 [help|h]     - このヘルプ"
            echo ""
            echo "📋 開発ワークフロー例:"
            echo "  1. $0 setup     # 初回セットアップ"
            echo "  2. $0 start     # 開発セッション開始"
            echo "  3. $0 status    # 状態確認"
            echo "  4. $0 reset     # 必要に応じてリセット"
            ;;
        *)
            log_info "不明なオプション: $1"
            echo "使用方法: $0 [setup|start|claude|status|reset|help]"
            exit 1
            ;;
    esac
}

main "$@"