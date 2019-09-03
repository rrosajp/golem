import asyncio
import unittest
from pathlib import Path

from golem_task_api import (
    ProviderAppClient,
    TaskApiService,
    RequestorAppClient
)
from golem_task_api.structs import Subtask
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase as TwistedTestCase

from golem.core.common import install_reactor
from golem.core.deferred import deferred_from_future
from golem.task.task_api import EnvironmentTaskApiService
from golem.tools.testwithreactor import uninstall_reactor
from tests.golem.envs.localhost import (
    LocalhostEnvironment,
    LocalhostConfig,
    LocalhostPrerequisites,
    LocalhostPayloadBuilder
)


class TestLocalhostEnv(TwistedTestCase):

    @classmethod
    def setUpClass(cls):
        try:
            uninstall_reactor()  # Because other tests don't clean up
        except AttributeError:
            pass
        install_reactor()

    @classmethod
    def tearDownClass(cls):
        uninstall_reactor()

    @staticmethod
    def _get_service(prereq: LocalhostPrerequisites) -> TaskApiService:
        env = LocalhostEnvironment(LocalhostConfig())
        return EnvironmentTaskApiService(
            env=env,
            payload_builder=LocalhostPayloadBuilder,
            prereq=prereq,
            shared_dir=Path('whatever')
        )

    # FIXME: https://github.com/golemfactory/golem/issues/4643
    @unittest.skip('To be fixed')
    @inlineCallbacks
    def test_compute(self):
        prereq = LocalhostPrerequisites(
            compute_results={'test_subtask': 'test_result'}
        )
        service = self._get_service(prereq)
        client_future = asyncio.ensure_future(ProviderAppClient.create(service))
        client = yield deferred_from_future(client_future)
        compute_future = asyncio.ensure_future(client.compute(
            task_id='test_task',
            subtask_id='test_subtask',
            subtask_params={'param': 'value'}
        ))
        result = yield deferred_from_future(compute_future)
        self.assertEqual(result, Path('test_result'))

    # FIXME: https://github.com/golemfactory/golem/issues/4643
    @unittest.skip('To be fixed')
    @inlineCallbacks
    def test_benchmark(self):
        prereq = LocalhostPrerequisites(benchmark_result=21.37)
        service = self._get_service(prereq)
        client_future = asyncio.ensure_future(ProviderAppClient.create(service))
        client = yield deferred_from_future(client_future)
        benchmark_future = asyncio.ensure_future(client.run_benchmark())
        result = yield deferred_from_future(benchmark_future)
        self.assertAlmostEqual(result, 21.37, places=5)

    # FIXME: https://github.com/golemfactory/golem/issues/4643
    @unittest.skip('To be fixed')
    @inlineCallbacks
    def test_subtasks(self):
        exp_subtask = Subtask(
            subtask_id='test_subtask',
            params={'param': 'value'},
            resources=['test_resource']
        )
        prereq = LocalhostPrerequisites(subtasks=[exp_subtask])
        service = self._get_service(prereq)
        client_future = asyncio.ensure_future(
            RequestorAppClient.create(service))
        client = yield deferred_from_future(client_future)

        pending_subtasks_future = asyncio.ensure_future(
            client.has_pending_subtasks('whatever')
        )
        pending_subtasks = yield deferred_from_future(pending_subtasks_future)
        self.assertTrue(pending_subtasks)

        subtask_future = asyncio.ensure_future(client.next_subtask('whatever'))
        subtask = yield deferred_from_future(subtask_future)
        self.assertEqual(subtask, exp_subtask)

        pending_subtasks_future = asyncio.ensure_future(
            client.has_pending_subtasks('whatever')
        )
        pending_subtasks = yield deferred_from_future(pending_subtasks_future)
        self.assertFalse(pending_subtasks)

        shutdown_future = asyncio.ensure_future(client.shutdown())
        yield deferred_from_future(shutdown_future)

    # FIXME: https://github.com/golemfactory/golem/issues/4643
    @unittest.skip('To be fixed')
    @inlineCallbacks
    def test_verify(self):
        prereq = LocalhostPrerequisites(verify_results={
            'good_subtask': (True, None),
            'bad_subtask': (False, 'test_error')
        })
        service = self._get_service(prereq)
        client_future = asyncio.ensure_future(
            RequestorAppClient.create(service))
        client = yield deferred_from_future(client_future)

        good_verify_future = asyncio.ensure_future(
            client.verify('test_task', 'good_subtask'))
        good_verify_result = yield deferred_from_future(good_verify_future)
        self.assertTrue(good_verify_result)

        bad_verify_future = asyncio.ensure_future(
            client.verify('test_task', 'bad_subtask'))
        bad_verify_result = yield deferred_from_future(bad_verify_future)
        self.assertFalse(bad_verify_result)

        shutdown_future = asyncio.ensure_future(client.shutdown())
        yield deferred_from_future(shutdown_future)