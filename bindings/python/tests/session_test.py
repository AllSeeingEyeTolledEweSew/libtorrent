import unittest

import libtorrent as lt


class AddTorrentParamsTest(unittest.TestCase):

    def test_fields(self) -> None:
        atp = lt.add_torrent_params()

        atp.version = 123
        self.assertEqual(atp.version, 123)
        atp.ti = lt.torrent_info(lt.sha1_hash())
        self.assertEqual(atp.ti.info_hashes().v1, lt.sha1_hash())
        atp.trackers = ["http://example.com/tr"]
        self.assertEqual(atp.trackers, ["http://example.com/tr"])
        atp.tracker_tiers = [1]
        self.assertEqual(atp.tracker_tiers, [1])
        atp.dht_nodes = [("0.1.2.3", 1234)]
        self.assertEqual(atp.dht_nodes, [("0.1.2.3", 1234)])
        atp.name = "test.txt"
        self.assertEqual(atp.name, "test.txt")
        atp.save_path = "."
        self.assertEqual(atp.save_path, ".")
        atp.storage_mode = lt.storage_mode_t.storage_mode_allocate
        self.assertEqual(atp.storage_mode, lt.storage_mode_t.storage_mode_allocate)
        atp.file_priorities = [1]
        self.assertEqual(atp.file_priorities, [1])
        atp.trackerid = "trackerid"
        self.assertEqual(atp.trackerid, "trackerid")
        atp.flags = lt.torrent_flags.default_flags
        self.assertEqual(atp.flags, lt.torrent_flags.default_flags)
        atp.max_uploads = 1
        self.assertEqual(atp.max_uploads, 1)
        atp.max_connections = 1
        self.assertEqual(atp.max_connections, 1)
        atp.upload_limit = 1024
        self.assertEqual(atp.upload_limit, 1024)
        atp.download_limit = 1024
        self.assertEqual(atp.download_limit, 1024)
        atp.total_uploaded = 1024
        self.assertEqual(atp.total_uploaded, 1024)
        atp.total_downloaded = 1024
        self.assertEqual(atp.total_downloaded, 1024)
        atp.active_time = 1234
        self.assertEqual(atp.active_time, 1234)
        atp.finished_time = 1234
        self.assertEqual(atp.finished_time, 1234)
        atp.seeding_time = 1234
        self.assertEqual(atp.seeding_time, 1234)
        atp.added_time = 1234
        self.assertEqual(atp.added_time, 1234)
        atp.completed_time = 1234
        self.assertEqual(atp.completed_time, 1234)
        atp.last_seen_complete = 1234
        self.assertEqual(atp.last_seen_complete, 1234)
        atp.last_download = 1234
        self.assertEqual(atp.last_download, 1234)
        atp.last_upload = 1234
        self.assertEqual(atp.last_upload, 1234)
        atp.num_complete = 10
        self.assertEqual(atp.num_complete, 10)
        atp.num_incomplete = 10
        self.assertEqual(atp.num_incomplete, 10)
        atp.num_downloaded = 10
        self.assertEqual(atp.num_downloaded, 10)
        atp.info_hashes = lt.info_hash_t(lt.sha1_hash())
        self.assertEqual(atp.info_hashes.v1, lt.sha1_hash())
        atp.url_seeds = ["http://example.com/seed"]
        self.assertEqual(atp.url_seeds, ["http://example.com/seed"])
        atp.peers = [("1.2.3.4", 4321)]
        self.assertEqual(atp.peers, [("1.2.3.4", 4321)])
        atp.banned_peers = [("2.3.4.5", 4321)]
        self.assertEqual(atp.banned_peers, [("2.3.4.5", 4321)])
        # atp.unfinished_pieces = {}
        self.assertEqual(atp.unfinished_pieces, {})
        atp.have_pieces = [True, False]
        self.assertEqual(atp.have_pieces, [True, False])
        atp.verified_pieces = [True, False]
        self.assertEqual(atp.verified_pieces, [True, False])
        atp.piece_priorities = [1]
        self.assertEqual(atp.piece_priorities, [1])
        # atp.renamed_files = {}
        self.assertEqual(atp.renamed_files, {})

    def test_name_assign_bytes_deprecated(self) -> None:
        atp = lt.add_torrent_params()

        with self.assertWarns(DeprecationWarning):
            atp.name = b"test.txt"

    def test_name_assign_bytes(self) -> None:
        atp = lt.add_torrent_params()

        with warnings.catch_warnings():
            atp.name = b"test.txt"
        self.assertEqual(atp.name, "test.txt")

    def test_name_bytes(self) -> None:
        atp = lt.add_torrent_params()

        atp.name_bytes = b"test1.txt"
        self.assertEqual(atp.name, "test1.txt")

        atp.name = "test2.txt"
        self.assertEqual(atp.name_bytes, b"test2.txt")

    def test_trackerid_assign_bytes_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            atp.trackerid = b"trackerid"

    def test_trackerid_assign_bytes(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            atp.trackerid = b"trackerid"
        self.assertEqual(atp.trackerid, "trackerid")

    def test_trackerid_bytes(self) -> None:
        atp = lt.add_torrent_params()

        atp.trackerid_bytes = b"trackerid1"
        self.assertEqual(atp.trackerid, "trackerid1")

        atp.trackerid = "trackerid2"
        self.assertEqual(atp.trackerid_bytes, b"trackerid2")

    def do_test_save_path_str(self, value:str) -> None:
        atp = lt.add_torrent_params()
        # test round-trip set-get
        atp.save_path = value
        self.assertEqual(atp.save_path, value)
        # encode to fastresume, test round-trip to encoded format
        encoded = lt.write_resume_data(atp)
        self.assertEqual(encoded[b"save_path"], os.fsencode(value))

    def test_save_path(self) -> None:
        # ascii
        self.do_test_save_path_str("test")

        # non-ascii
        self.do_test_save_path_str("\u1234")

    def test_save_path_surrogate(self) -> None:
        # surrogate
        self.do_test_save_path_str("\udcff")

    def test_save_path_bytes_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            atp.save_path = b"test"

    def test_save_path_bytes(self) -> None:
        atp = lt.add_torrent_params()
        
        # ascii
        with warnings.catch_warnings():
            atp.save_path = b"test"
        self.assertEqual(atp.save_path, "test")

        # non-ascii
        with warnings.catch_warnings():
            atp.save_path = "\u1234".encode()
        self.assertEqual(atp.save_path, "\u1234")

    def test_info_hash_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            self.assertTrue(atp.info_hash.is_all_zeros())
        with self.assertWarns(DeprecationWarning):
            atp.info_hash = lt.sha1_hash(lib.get_random_bytes(20))

    def test_info_hash(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            self.assertTrue(atp.info_hash.is_all_zeros())

    def test_http_seeds_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(atp.http_seeds, [])
        with self.assertWarns(DeprecationWarning):
            atp.http_seeds = ["http://example.com/seed"]

    def test_http_seeds(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            atp.http_seeds = ["http://example.com/seed"]
            self.assertEqual(atp.http_seeds, ["http://example.com/seed"])

    def test_unfinished_pieces(self) -> None:
        atp = lt.add_torrent_params()
        atp.unfinished_pieces = {}
        atp.unfinished_pieces = {1: [True, False]}

    def test_merkle_tree_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(atp.merkle_tree, [])
        with self.assertWarns(DeprecationWarning):
            atp.merkle_tree = [lt.sha1_hash()]

    def test_merkle_tree(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            atp.merkle_tree = [lt.sha1_hash()]
            self.assertEqual(atp.merkle_tree, [lt.sha1_hash()])

    def test_url_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(atp.url, "")
        with self.assertWarns(DeprecationWarning):
            atp.url = "http://example.com/torrent"

    def test_url(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            atp.url = "http://example.com/torrent"
            self.assertEqual(atp.url, "http://example.com/torrent")

    def test_resume_data_deprecated(self) -> None:
        atp = lt.add_torrent_params()
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(atp.resume_data, [])
        with self.assertWarns(DeprecationWarning):
            atp.resume_data = [1]

    def test_resume_data(self) -> None:
        atp = lt.add_torrent_params()
        with warnings.catch_warnings():
            atp.resume_data = [1]
            self.assertEqual(atp.resume_data, [1])

    def test_renamed_files(self) -> None:
        TODO

    def test_renamed_files_bytes(self) -> None:
        TODO


class ResumeDataTest(unittest.TestCase):

    def do_test_round_trip(self, atp:lt.add_torrent_params) -> None:
        first = lt.write_resume_data(atp)
        second = lt.write_resume_data(lt.read_resume_data(lt.write_resume_data_buf(atp)))

        self.assertEqual(first, second)

    def test_round_trip(self) -> None:
        atp = lt.add_torrent_params()
        atp.name = "test"
        self.do_test_round_trip(atp)

    def test_limit_decode_depth(self) -> None:
        atp = lt.add_torrent_params()
        buf = lt.write_resume_data_buf(atp)
        with self.assertRaises(RuntimeError):
            lt.read_resume_data(buf, {b"max_decode_depth": 1})

    def test_limit_decode_tokens(self) -> None:
        atp = lt.add_torrent_params()
        buf = lt.write_resume_data_buf(atp)
        with self.assertRaises(RuntimeError):
            lt.read_resume_data(buf, {b"max_decode_tokens": 1})

    def test_limit_pieces(self) -> None:
        atp = lt.add_torrent_params()
        atp.ti = lt.torrent_info(
                {
                    b"info": {
                        b"name": b"test.txt",
                        b"length": 1234000,
                        b"piece length": 16384,
                        b"pieces": b"aaaaaaaaaaaaaaaaaaaa" * (1234000 // 16384 + 1),
                    }
                    }
            )
        buf = lt.write_resume_data_buf(atp)
        with self.assertRaises(RuntimeError):
            lt.read_resume_data(buf, {b"max_pieces": 1})


class ConstructorTest(unittest.TestCase):

    TODO
    prebuilt_settings_packs


class DhtTest(unittest.TestCase):

    add_dht_node
    add_dht_router
    is_dht_running
    set_dht_settings
    get_dht_settings
    dht_get_immutable_item
    dht_get_mutable_item
    dht_put_immutable_item
    dht_put_mutable_item
    dht_get_peers
    dht_announce
    dht_live_nodes
    dht_sample_infohashes
    dht_state


class AlertTest(unittest.TestCase):
    pop_alerts
    wait_for_alert
    set_alert_notify
    set_alert_fd


class SessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.session = lt.session(lib.get_isolated_settings())

    def test_post_alerts(self) -> None:
        post_torrent_updates
        post_dht_stats
        post_session_stats

    def test_add_torrent(self) -> None:
        add_torrent
        async_add_torrent

    def test_remove_torrent(self) -> None:
        remove_torrent
        # with and without remove data

    def test_status(self) -> None:
        status

    def test_settings(self) -> None:
        prebuilt_settings_packs
        get_settings
        apply_settings
        local_download_rate_limit
        local_upload_rate_limit
        download_rate_limit
        upload_rate_limit
        max_uploads
        max_connections
        set_dht_proxy
        dht_proxy
        set_max_half_open_connections
        set_alert_queue_size_limit
        set_alert_mask
        set_peer_proxy
        set_tracker_proxy
        set_web_seed_proxy
        peer_proxy
        tracker_proxy
        web_seed_proxy
        set_proxy
        proxy

    def test_pe_settings(self) -> None:
        get_pe_settings
        set_pe_settings

    def test_state(self) -> None:
        load_state
        save_state

    def test_extensions(self) -> None:
        add_extension

    def test_i2p(self) -> None:
        set_i2p_proxy
        i2p_proxy

    def test_ip_filter(self) -> None:
        set_ip_filter
        get_ip_filter

    def test_get_torrents(self) -> None:
        find_torrent
        get_torrents

    def test_torrent_status(self) -> None:
        get_torrent_status
        refresh_torrent_status

    def test_pause(self) -> None:
        pause
        resume
        is_paused

    def test_ports(self) -> None:
        add_port_mapping
        delete_port_mapping
        reopen_network_sockets
        listen_on
        is_listening
        listen_port
        outgoing_ports

    def test_peer_class(self) -> None:
        set_peer_class_filter
        set_peer_class_type_filter
        create_peer_class
        delete_peer_class
        get_peer_class
        set_peer_class

    def test_fields(self) -> None:
        id
        set_peer_id
        num_connections

    def test_components(self) -> None:
        upnp
        lsd
        natpmp
        dht


class SessionStatsTest(unittest.TestCase):

    TODO
