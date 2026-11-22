from pathlib import Path

import pytest

from agent_hub.attempts import announce, create_binding
from agent_hub.hooks import HookQueue
from agent_hub.storage import Store


def test_three_local_bindings_attach_to_one_task_and_reconcile(tmp_path):
    store = Store(tmp_path/'central.db')
    configs = []
    for who, action in [('A','start'),('B','handoff'),('C','verify')]:
        root = tmp_path / who / 'project'; root.mkdir(parents=True)
        profile = dict(project='repo',account='account-'+who,host=who,window='same-title',generation='first',
                       tool={'A':'codex','B':'claude','C':'grok'}[who],project_root=str(root),state_dir=str(tmp_path/who/'private'))
        output = tmp_path / who / 'binding.json'
        cfg = create_binding(profile,output,action,task_id='task',previous='A' if who=='B' else None,
                             attempt_id=who,artifact='sha:fixture')
        configs.append(cfg)
        assert announce(cfg) == announce(cfg)
        assert HookQueue(cfg).flush(lambda _,arg:store.report_step(arg['project'],who,arg['event'])) == 1
        with pytest.raises(FileExistsError):
            create_binding(profile,output,'start')
    assert store.get_task_status('repo','task')['primary_attempt_id'] == 'B'
    assert len(store.get_task_status('repo','task')['attempts']) == 3
    assert len(list(Path(configs[0]['project_root']).rglob('*.md'))) == 1
