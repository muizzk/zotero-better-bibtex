from steps.zotero import Zotero
from munch import *
from behave import given, when, then, use_step_matcher
import urllib.request
import json
import zotero
import time
import os
from hamcrest import assert_that, equal_to
from steps.utils import assert_equal_diff, expand_scenario_variables

import pathlib
for d in pathlib.Path(__file__).resolve().parents:
  if os.path.exists(os.path.join(d, 'behave.ini')):
    ROOT = d
    break

@step('I set preference {pref} to {value}')
def step_impl(context, pref, value):
  # bit of a cheat...
  if pref.endswith('.postscript'):
    value = expand_scenario_variables(context, value)
  context.zotero.preferences[pref] = context.zotero.preferences.parse(value)

@step(r'I restart Zotero with from "{db}" + "{source}"')
def step_impl(context, source, db):
  source = expand_scenario_variables(context, source)
  context.imported = source

  with open(os.path.join(ROOT, 'test', 'fixtures', source)) as f:
    data = json.load(f)
    items = data['items']
    #references = sum([ 1 + len(item.get('attachments', [])) + len(item.get('notes', [])) for item in items ])
    references = len(items)

  dbs = os.path.join(ROOT, 'test', 'db', db)
  if not os.path.exists(dbs): os.makedirs(dbs)
  zotero = os.path.join(dbs, 'zotero.sqlite')
  if not os.path.exists(zotero):
    urllib.request.urlretrieve(f'https://github.com/retorquere/zotero-better-bibtex/releases/download/test-database/{db}.zotero.sqlite', zotero)
  bbt = os.path.join(dbs, 'better-bibtex.sqlite')
  if not os.path.exists(bbt):
    urllib.request.urlretrieve(f'https://github.com/retorquere/zotero-better-bibtex/releases/download/test-database/{db}.better-bibtex.sqlite', bbt)

  timeout = context.zotero.timeout
  context.zotero.shutdown()
  context.zotero = Zotero(context.config.userdata, db=Munch(zotero=zotero, bbt=bbt))
  context.zotero.timeout = timeout
  assert_that(context.zotero.execute('return await Zotero.BetterBibTeX.TestSupport.librarySize()'), equal_to(references))

  context.zotero.import_file(context, source, items=False)

@step(r'I import {references:d} references from "{source}"')
def step_impl(context, references, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source), equal_to(references))

@step(r'I import 1 reference from "{source}" into "{collection}"')
def step_impl(context, source, collection):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source, collection), equal_to(1))

@step(r'I import 1 reference from "{source}"')
def step_impl(context, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source), equal_to(1))

@given(u'I import 1 reference with 1 attachment from "{source}"')
def step_impl(context, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source), equal_to(1))

@step(r'I import {references:d} references with {attachments:d} attachments from "{source}" into a new collection')
def step_impl(context, references, attachments, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source, True), equal_to(references))

@step(r'I import {references:d} references from "{source}" into a new collection')
def step_impl(context, references, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source, True), equal_to(references))

@step(r'I import {references:d} references with {attachments:d} attachments from "{source}"')
def step_impl(context, references, attachments, source):
  source = expand_scenario_variables(context, source)
  context.imported = source
  assert_that(context.zotero.import_file(context, source), equal_to(references))

def export_library(context, translator='BetterBibTeX JSON', collection=None, expected=None, output=None, displayOption=None, timeout=None, resetCache=False):
  expected = expand_scenario_variables(context, expected)
  displayOptions = { **context.displayOptions }
  if displayOption: displayOptions[displayOption] = True

  start = time.time()
  context.zotero.export_library(
    displayOptions = displayOptions,
    translator = translator,
    output = output,
    expected = expected,
    resetCache = resetCache,
    collection = collection
  )
  runtime = time.time() - start

  if context.max_export_time is not None:
    assert(runtime < context.max_export_time), f'Export runtime of {runtime} exceeded set maximum of {context.max_export_time}'

@step(u'an auto-export to "{output}" using "{translator}" should match "{expected}"')
def step_impl(context, translator, output, expected):
  export_library(context,
    translator=translator,
    expected=expected,
    output=output,
    displayOption='keepUpdated',
    resetCache = True
  )

@then(u'an auto-export of "{collection}" to "{output}" using "{translator}" should match "{expected}"')
def step_impl(context, translator, collection, output, expected):
  export_library(context,
    displayOption = 'keepUpdated',
    translator = translator,
    collection = collection,
    output = output,
    expected = expected,
    resetCache = True
  )

@step('an export using "{translator}" with {displayOption} on should match "{expected}"')
def step_impl(context, translator, displayOption, expected):
  export_library(context,
    displayOption = displayOption,
    translator = translator,
    expected = expected
  )

@step('an export using "{translator}" should match "{expected}"')
def step_impl(context, translator, expected):
  export_library(context,
    translator = translator,
    expected = expected
  )

@step('an export using "{translator}" should match "{expected}", but take no more than {seconds:d} seconds')
def step_impl(context, translator, expected, seconds):
  export_library(context,
    translator = translator,
    expected = expected,
    timeout = seconds
  )

@step('the library should match "{expected}"')
def step_impl(context, expected):
  export_library(context, expected = expected)

@when(u'I select the first item where {field} = "{value}"')
def step_impl(context, field, value):
  context.selected.append(context.zotero.execute('return await Zotero.BetterBibTeX.TestSupport.find({is: value})', value=value))
  context.zotero.execute('await Zotero.BetterBibTeX.TestSupport.select(ids)', ids=context.selected)
  time.sleep(3)

@when(u'I remove the selected item')
def step_impl(context):
  assert len(context.selected) == 1
  context.zotero.execute('await Zotero.Items.trashTx([id])', id=context.selected[0])

@when(u'I remove the selected items')
def step_impl(context):
  assert len(context.selected) > 0
  context.zotero.execute('await Zotero.Items.trashTx(ids)', ids=context.selected)

@when(u'I merge the selected items')
def step_impl(context):
  assert len(context.selected) > 1
  context.zotero.execute('return await Zotero.BetterBibTeX.TestSupport.merge(selected)', selected=context.selected)

@when(u'I pick "{title}" for CAYW')
def step_impl(context, title):
  pick = zotero.Pick(id = context.zotero.execute('return await Zotero.BetterBibTeX.TestSupport.find({contains: title})', title=title))
  assert pick['id'] is not None

  pick[context.table.headings[0]] = context.table.headings[1]
  for row in context.table:
    pick[row[0]] = row[1]
  context.picked.append(dict(pick))

@then(u'the picks for "{fmt}" should be "{expected}"')
def step_impl(context, fmt, expected):
  found = context.zotero.execute('return await Zotero.BetterBibTeX.TestSupport.pick(fmt, picks)', fmt=fmt, picks=context.picked)
  assert_equal_diff(expected.strip(), found.strip())

@when(u'I {change} the citation key')
def step_impl(context, change):
  assert change in ['pin', 'unpin', 'refresh']
  assert len(context.selected) == 1
  context.zotero.execute('await Zotero.BetterBibTeX.TestSupport.pinCiteKey(itemID, action)', itemID=context.selected[0], action=change)

@when(u'I {change} all citation keys')
def step_impl(context, change):
  assert change in ['pin', 'unpin', 'refresh']
  context.zotero.execute('await Zotero.BetterBibTeX.TestSupport.pinCiteKey(null, action)', action=change)

@then(u'"{found}" should match "{expected}"')
def step_impl(context, expected, found):
  expected = expand_scenario_variables(context, expected)
  if expected[0] != '/': expected = os.path.join(ROOT, 'test/fixtures', expected)
  with open(expected) as f:
    expected = f.read()

  if found[0] != '/': found = os.path.join(ROOT, 'test/fixtures', found)
  with open(found) as f:
    found = f.read()

  assert_equal_diff(expected.strip(), found.strip())

@when(u'I wait {seconds:d} seconds')
def step_impl(context, seconds):
  time.sleep(seconds)

