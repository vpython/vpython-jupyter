"""Scene journal: enough recorded state to rebuild any frontend at attach.

Frontends are ephemeral (Colab re-renders output frames on scroll; VS Code
can evict outputs; pages reload). The journal records every constructor cmd
and every attribute ever touched, and builds a replay package — reset, all
constructors, current attribute values — so a brand-new frontend instance
can reconstruct the scene from nothing.
"""
from vpython._scene_journal import SceneJournal


def test_records_constructors_in_creation_order():
    j = SceneJournal()
    j.record_cmd({'cmd': 'canvas', 'idx': 1, 'width': 640})
    j.record_cmd({'cmd': 'sphere', 'idx': 2, 'canvas': 1})
    j.record_cmd({'cmd': 'box', 'idx': 3, 'canvas': 1})
    cmds = j.constructors()
    assert [c['cmd'] for c in cmds] == ['canvas', 'sphere', 'box']


def test_late_enriched_constructor_keys_are_included_at_replay():
    # canvas builds its cmd incrementally AFTER appendcmd; the journal must
    # reflect the enriched dict, not a bare record-time snapshot.
    j = SceneJournal()
    cmd = {'cmd': 'canvas', 'idx': 1}
    j.record_cmd(cmd)
    cmd['ambient'] = [0.2, 0.2, 0.2]
    assert j.constructors()[0]['ambient'] == [0.2, 0.2, 0.2]
    # but the returned list is still a copy: mutating it is inert
    j.constructors()[0]['hacked'] = True
    assert 'hacked' not in j.constructors()[0]


def test_delete_removes_object_and_its_dirty_attrs():
    j = SceneJournal()
    j.record_cmd({'cmd': 'sphere', 'idx': 2})
    j.record_attr(2, 'pos')
    j.record_cmd({'cmd': 'delete', 'idx': 2})
    assert j.constructors() == []
    assert j.dirty_attrs() == set()


def test_dirty_attrs_accumulate_across_flushes():
    j = SceneJournal()
    j.record_cmd({'cmd': 'sphere', 'idx': 2})
    j.record_attr(2, 'pos')
    j.record_attr(2, 'color')
    j.record_attr(2, 'pos')  # repeated set: still one entry
    assert j.dirty_attrs() == {(2, 'pos'), (2, 'color')}


def test_replay_objdata_reset_constructors_then_current_attr_values():
    j = SceneJournal()
    j.record_cmd({'cmd': 'canvas', 'idx': 1})
    j.record_cmd({'cmd': 'sphere', 'idx': 2, 'canvas': 1})
    j.record_attr(2, 'pos')
    j.record_attr(9, 'pos')  # object the registry no longer knows: skipped

    values = {(2, 'pos'): [1, 2, 3]}
    def value_of(idx, attr):
        return values.get((idx, attr))

    objdata = j.replay_objdata(value_of)
    assert objdata['cmds'][0] == {'cmd': 'reset', 'idx': -1}
    assert [c['cmd'] for c in objdata['cmds'][1:]] == ['canvas', 'sphere']
    assert objdata['attrs'] == {2: {'pos': [1, 2, 3]}}
    assert objdata['methods'] == []


def test_empty_journal_still_replays_a_bare_reset():
    j = SceneJournal()
    objdata = j.replay_objdata(lambda i, a: None)
    assert objdata['cmds'] == [{'cmd': 'reset', 'idx': -1}]
    assert objdata['attrs'] == {}


def test_replay_preserves_live_emission_order_of_followups():
    # THE Colab dim-scene bug: canvas construction emits, in this order,
    #   canvas ctor -> lights='empty_list' (wipe glow's built-in defaults)
    #   -> two distant_light ctors (the standard lighting).
    # Replaying constructors-then-extras moves the wipe AFTER the standard
    # lights, deleting them: the scene renders ambient-only (dim). Replay
    # must preserve the original emission order.
    j = SceneJournal()
    j.record_cmd({'cmd': 'canvas', 'idx': 1})
    j.record_cmd({'lights': 'empty_list', 'idx': 1})
    j.record_cmd({'cmd': 'distant_light', 'idx': 2, 'canvas': 1})
    j.record_cmd({'cmd': 'distant_light', 'idx': 3, 'canvas': 1})
    j.record_cmd({'cmd': 'sphere', 'idx': 4, 'canvas': 1})
    cmds = j.replay_objdata(lambda i, a: None)['cmds']
    assert cmds[0] == {'cmd': 'reset', 'idx': -1}
    wipe_at = next(i for i, c in enumerate(cmds)
                   if c.get('lights') == 'empty_list')
    light_at = [i for i, c in enumerate(cmds)
                if c.get('cmd') == 'distant_light']
    assert wipe_at < min(light_at), (
        'lights wipe replayed after the standard lights: scene goes dim')


def test_followup_cmds_do_not_clobber_the_constructor():
    j = SceneJournal()
    j.record_cmd({'cmd': 'canvas', 'idx': 1})
    j.record_cmd({'title': 'my scene', 'idx': 1})  # canvas.title follow-up
    assert [c['cmd'] for c in j.constructors()] == ['canvas']
    objdata = j.replay_objdata(lambda i, a: None)
    assert objdata['cmds'][1]['cmd'] == 'canvas'
    assert objdata['cmds'][2] == {'title': 'my scene', 'idx': 1}
