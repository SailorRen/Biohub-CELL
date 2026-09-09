#!/usr/bin/env python3
"""Read known public topics and comments only; save raw text under ignored downloads."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'downloads/20260909_public_research/discussions'
RAW.mkdir(parents=True, exist_ok=True)
IDS = [738217, 740145, 740103, 739685, 739516, 739352, 739731, 739278, 734330]

def main():
    from kaggle import api
    from kagglesdk.discussions.types.discussions_api_service import ApiGetTopicRequest, ApiListCommentsRequest
    inventory = []
    for topic_id in IDS:
        out = {'id': topic_id, 'url': f'https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/{topic_id}',
               'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'platform_writes': 0}
        try:
            q = ApiGetTopicRequest(); q.id = topic_id
            with api.build_kaggle_client() as client:
                topic = client.discussions.discussion_api_client.get_topic(q).topic
            out['topic'] = topic.to_dict()
            assert topic.id == topic_id
            pages, token, seen = [], '', set()
            for _ in range(5):
                q = ApiListCommentsRequest(); q.topic_id = topic_id; q.page_size = 100; q.page_token = token
                with api.build_kaggle_client() as client:
                    response = client.discussions.discussion_api_client.list_comments(q)
                pages.append(response.to_dict())
                token = response.next_page_token or ''
                if not token: break
                if token in seen: raise RuntimeError('Repeated pagination token')
                seen.add(token)
            out['comment_pages'] = pages
            out['comments_pagination_complete'] = not token
            out['status'] = 'TEXT_ACQUIRED_NOT_YET_REVIEWED'
        except Exception as error:
            out['status'] = 'READ_ERROR'
            out['error_type'] = type(error).__name__
        path = RAW / f'{topic_id}.json'
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + '\n')
        item = {k: out[k] for k in ['id','url','observed_at_utc','status']}
        item.update({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'bytes': path.stat().st_size, 'title': out.get('topic', {}).get('title'),
                     'comments_pagination_complete': out.get('comments_pagination_complete', False)})
        inventory.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    (Path(__file__).parent / 'discussion_acquisition.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__': main()
