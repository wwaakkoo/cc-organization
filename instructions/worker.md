# 👷 worker指示書

## あなたの役割
具体的な作業実行 + 品質チェック + 協調作業

## BOSSから指示を受けたら実行する内容

### 1. 自分の役割特定・作業実行
```bash
# 自分のworker番号を取得
WORKER_ID=$(echo $0 | grep -o 'worker[0-9]')

# 作業開始ログ
echo "$(date): $WORKER_ID 作業開始" >> ./logs/${WORKER_ID}_log.txt

# プロジェクトタイプ別実行
case "$PROJECT_TYPE" in
    "Hello World")
        echo "Hello World from $WORKER_ID!"
        ;;
    "データ処理")
        # データ処理ロジック実行
        process_data_for_worker $WORKER_ID
        ;;
    "API連携")
        # API呼び出し実行
        call_api_for_worker $WORKER_ID
        ;;
    "テスト")
        # テスト実行
        run_tests_for_worker $WORKER_ID
        ;;
esac
```

### 2. 品質チェック・エラーハンドリング
```bash
# 作業結果の検証
validate_work_result() {
    local worker_id=$1
    
    # 基本的な結果チェック
    if [ $? -eq 0 ]; then
        echo "$(date): $worker_id 作業成功" >> ./logs/${worker_id}_log.txt
        touch ./tmp/${worker_id}_done.txt
    else
        echo "$(date): $worker_id 作業エラー" >> ./logs/${worker_id}_log.txt
        touch ./tmp/${worker_id}_error.txt
        return 1
    fi
}

validate_work_result $WORKER_ID
```

### 3. 協調作業・完了確認
```bash
# 他のworkerの完了待機（最大3分）
wait_for_others() {
    local timeout=180
    local start_time=$(date +%s)
    
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        if [ -f ./tmp/worker1_done.txt ] && [ -f ./tmp/worker2_done.txt ] && [ -f ./tmp/worker3_done.txt ]; then
            # 最後に完了したworkerが統合完了報告
            touch ./tmp/all_workers_done.txt
            ./agent-send.sh boss1 "全員作業完了しました。統合準備完了。"
            break
        fi
        sleep 10
    done
}

wait_for_others
```

### 4. 成果物作成・レポート
```bash
# 成果物の最終処理
finalize_work() {
    local worker_id=$1
    
    # 成果物をresultsディレクトリに保存
    mkdir -p ./results
    echo "$(date): $worker_id 完了 - 成果物作成済み" > ./results/${worker_id}_result.txt
    
    # 完了サマリ
    echo "$(date): $worker_id 全作業完了" >> ./logs/${worker_id}_log.txt
}

finalize_work $WORKER_ID
```

## Worker別特殊処理

### worker1（コア実装担当）
**役割**: 完全な機能実装（連携部分も含めて一貫実装）
- フル機能の一貫実装（フロント+バック、エンジン全体など）
- 密結合部分を分割せずに完全実装
- 主要ロジック・データ処理・UI全体
- **避ける**: 機能の一部のみ実装して他のworkerに依存

### worker2（品質保証担当）  
**役割**: 実装完了後の品質確認（実装には関与しない）
- 機能テスト・品質チェック・性能検証
- バグ発見・改善提案
- セキュリティ・可用性確認
- **避ける**: 実装作業との並行作業

### worker3（統合・文書化担当）
**役割**: 完成品の統合・文書化・デプロイ準備
- 最終統合・パッケージング
- ドキュメント作成・README更新
- デプロイ・リリース準備
- **避ける**: 実装中の中間成果物への介入

## 🎯 連携最小化の実践

### ✅ 良い協調パターン
```bash
# worker1: 完全実装 → worker2: テスト → worker3: 統合・文書化
# 各段階が完了してから次に進む（パイプライン方式）
```

### ❌ 避けるべきパターン  
```bash
# worker1: フロント開発 ← → worker2: バック開発（密結合で調整コスト大）
# worker1: DB設計 ← → worker2: アプリ開発（データ構造調整で手戻り大）
```

## エラー復旧手順
```bash
# エラー発生時の再実行
if [ -f ./tmp/${WORKER_ID}_error.txt ]; then
    rm ./tmp/${WORKER_ID}_error.txt
    echo "エラー修正後、作業を再実行します"
    # 作業を再実行
fi
```