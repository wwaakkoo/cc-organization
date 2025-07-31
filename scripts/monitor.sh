#!/bin/bash

# 🔍 Multi-Agent システム監視ツール

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# システム状態監視
monitor_system() {
    clear
    echo "🔍 Multi-Agent システム監視ダッシュボード"
    echo "========================================"
    echo ""
    
    # tmuxセッション状態
    log_info "📺 Tmux Sessions:"
    if tmux list-sessions 2>/dev/null; then
        echo ""
    else
        log_warning "Tmuxセッションが見つかりません"
        echo ""
    fi
    
    # エージェント状態
    log_info "🤖 Agent Status:"
    ./agent-send.sh --list
    echo ""
    
    # ファイル状態監視
    log_info "📁 Work Files Status:"
    echo "  完了ファイル:"
    ls -la ./tmp/*_done.txt 2>/dev/null | head -10 || echo "    なし"
    echo ""
    echo "  エラーファイル:"
    ls -la ./tmp/*_error.txt 2>/dev/null | head -5 || echo "    なし"
    echo ""
    
    # ログ監視
    log_info "📝 Recent Logs (最新5件):"
    if [ -f "./logs/send_log.txt" ]; then
        tail -5 ./logs/send_log.txt
    else
        echo "    ログファイルなし"
    fi
    echo ""
    
    # プロセス監視
    log_info "💻 Claude Code Processes:"
    ps aux | grep -i claude | grep -v grep | head -5 || echo "    実行中のプロセスなし"
    echo ""
}

# ログ分析
analyze_logs() {
    echo "📊 ログ分析レポート"
    echo "=================="
    echo ""
    
    if [ -f "./logs/send_log.txt" ]; then
        log_info "メッセージ送信統計:"
        echo "  総送信数: $(wc -l < ./logs/send_log.txt)"
        echo "  成功: $(grep -c SUCCESS ./logs/send_log.txt 2>/dev/null || echo 0)"
        echo "  失敗: $(grep -c FAILED ./logs/send_log.txt 2>/dev/null || echo 0)"
        echo ""
        
        log_info "エージェント別送信数:"
        grep -o '[a-z0-9]*:' ./logs/send_log.txt | sort | uniq -c | sort -nr
        echo ""
    fi
    
    log_info "エラー分析:"
    if ls ./tmp/*_error.txt 1> /dev/null 2>&1; then
        for error_file in ./tmp/*_error.txt; do
            agent=$(basename "$error_file" _error.txt)
            log_error "$agent でエラー発生"
        done
    else
        log_success "エラーファイルなし"
    fi
}

# システムクリーンアップ
cleanup_system() {
    log_info "🧹 システムクリーンアップ開始"
    
    # 古いログファイル削除（7日以上）
    find ./logs -name "*.txt" -mtime +7 -delete 2>/dev/null || true
    
    # 完了ファイル削除
    rm -f ./tmp/*_done.txt ./tmp/*_error.txt ./tmp/*_status.txt 2>/dev/null || true
    
    # 空のディレクトリ削除
    find ./results -type d -empty -delete 2>/dev/null || true
    
    log_success "クリーンアップ完了"
}

# メイン処理
main() {
    case "${1:-monitor}" in
        "monitor"|"m")
            while true; do
                monitor_system
                echo "🔄 10秒後に更新... (Ctrl+C で終了)"
                sleep 10
            done
            ;;
        "analyze"|"a")
            analyze_logs
            ;;
        "cleanup"|"c")
            cleanup_system
            ;;
        "once"|"o")
            monitor_system
            ;;
        "help"|"h"|"--help")
            echo "使用方法:"
            echo "  $0 [monitor|m]  - 継続監視（デフォルト）"
            echo "  $0 [once|o]     - 1回だけ表示"
            echo "  $0 [analyze|a]  - ログ分析"
            echo "  $0 [cleanup|c]  - システムクリーンアップ"
            echo "  $0 [help|h]     - このヘルプ"
            ;;
        *)
            log_error "不明なオプション: $1"
            echo "使用方法: $0 [monitor|analyze|cleanup|help]"
            exit 1
            ;;
    esac
}

main "$@"