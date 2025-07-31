#!/bin/bash

# 🚀 Agent間メッセージ送信スクリプト

# tmuxのbase-indexとpane-base-indexを動的に取得
get_tmux_indices() {
    local session="$1"
    local window_index=$(tmux show-options -t "$session" -g base-index 2>/dev/null | awk '{print $2}')
    local pane_index=$(tmux show-options -t "$session" -g pane-base-index 2>/dev/null | awk '{print $2}')

    # デフォルト値
    window_index=${window_index:-0}
    pane_index=${pane_index:-0}

    echo "$window_index $pane_index"
}

# エージェント→tmuxターゲット マッピング
get_agent_target() {
    case "$1" in
        "president") echo "president" ;;
        "boss1"|"worker1"|"worker2"|"worker3")
            # multiagentセッションのindexを動的に取得
            if tmux has-session -t multiagent 2>/dev/null; then
                local indices=($(get_tmux_indices multiagent))
                local window_index=${indices[0]}
                local pane_index=${indices[1]}

                # window名で取得（base-indexに依存しない）
                local window_name="agents"

                # pane番号を計算
                case "$1" in
                    "boss1") echo "multiagent:$window_name.$((pane_index))" ;;
                    "worker1") echo "multiagent:$window_name.$((pane_index + 1))" ;;
                    "worker2") echo "multiagent:$window_name.$((pane_index + 2))" ;;
                    "worker3") echo "multiagent:$window_name.$((pane_index + 3))" ;;
                esac
            else
                echo ""
            fi
            ;;
        *) echo "" ;;
    esac
}

show_usage() {
    cat << EOF
🤖 Agent間メッセージ送信

使用方法:
  $0 [エージェント名] [メッセージ]
  $0 --list

利用可能エージェント:
  president - プロジェクト統括責任者
  boss1     - チームリーダー  
  worker1   - 実行担当者A
  worker2   - 実行担当者B
  worker3   - 実行担当者C

使用例:
  $0 president "指示書に従って"
  $0 boss1 "Hello World プロジェクト開始指示"
  $0 worker1 "作業完了しました"
EOF
}

# エージェント一覧表示
show_agents() {
    echo "📋 利用可能なエージェント:"
    echo "=========================="

    # presidentセッション確認
    if tmux has-session -t president 2>/dev/null; then
        echo "  president → president       (プロジェクト統括責任者)"
    else
        echo "  president → [未起動]        (プロジェクト統括責任者)"
    fi

    # multiagentセッション確認
    if tmux has-session -t multiagent 2>/dev/null; then
        local boss1_target=$(get_agent_target "boss1")
        local worker1_target=$(get_agent_target "worker1")
        local worker2_target=$(get_agent_target "worker2")
        local worker3_target=$(get_agent_target "worker3")

        echo "  boss1     → ${boss1_target:-[エラー]}  (チームリーダー)"
        echo "  worker1   → ${worker1_target:-[エラー]}  (実行担当者A)"
        echo "  worker2   → ${worker2_target:-[エラー]}  (実行担当者B)"
        echo "  worker3   → ${worker3_target:-[エラー]}  (実行担当者C)"
    else
        echo "  boss1     → [未起動]        (チームリーダー)"
        echo "  worker1   → [未起動]        (実行担当者A)"
        echo "  worker2   → [未起動]        (実行担当者B)"
        echo "  worker3   → [未起動]        (実行担当者C)"
    fi
}

# ログ記録（拡張版）
log_send() {
    local agent="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local status="${3:-SUCCESS}"
    
    mkdir -p logs
    echo "[$timestamp] $agent: $status - \"$message\"" >> logs/send_log.txt
    
    # エージェント別ログも作成
    echo "[$timestamp] SENT: \"$message\"" >> logs/${agent}_log.txt
}

# メッセージ送信（拡張版）
send_message() {
    local target="$1"
    local message="$2"
    local retry_count=0
    local max_retries=3
    
    echo "📤 送信中: $target ← '$message'"
    
    while [ $retry_count -lt $max_retries ]; do
        # Claude Codeのプロンプトを一度クリア
        tmux send-keys -t "$target" C-c
        sleep 0.3
        
        # メッセージ送信
        tmux send-keys -t "$target" "$message"
        sleep 0.1
        
        # エンター押下
        tmux send-keys -t "$target" C-m
        sleep 0.5
        
        # 送信成功確認（基本的には成功とみなす）
        if [ $? -eq 0 ]; then
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        echo "⚠️  送信失敗 (試行 $retry_count/$max_retries)"
        sleep 1
    done
    
    echo "❌ 送信失敗: $target へのメッセージ送信に失敗しました"
    return 1
}

# ターゲット存在確認
check_target() {
    local target="$1"
    local session_name="${target%%:*}"
    
    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        echo "❌ セッション '$session_name' が見つかりません"
        return 1
    fi
    
    return 0
}

# メイン処理
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    # --listオプション
    if [[ "$1" == "--list" ]]; then
        show_agents
        exit 0
    fi
    
    if [[ $# -lt 2 ]]; then
        show_usage
        exit 1
    fi
    
    local agent_name="$1"
    local message="$2"
    
    # エージェントターゲット取得
    local target
    target=$(get_agent_target "$agent_name")
    
    if [[ -z "$target" ]]; then
        echo "❌ エラー: 不明なエージェント '$agent_name'"
        echo "利用可能エージェント: $0 --list"
        exit 1
    fi
    
    # ターゲット確認
    if ! check_target "$target"; then
        exit 1
    fi
    
    # メッセージ送信
    if send_message "$target" "$message"; then
        # ログ記録（成功）
        log_send "$agent_name" "$message" "SUCCESS"
        echo "✅ 送信完了: $agent_name に '$message'"
    else
        # ログ記録（失敗）
        log_send "$agent_name" "$message" "FAILED"
        echo "❌ 送信失敗: $agent_name に '$message'"
        exit 1
    fi
    
    return 0
}

main "$@" 