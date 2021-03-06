__author__ = 'chris'

import json
import random
import time
import nacl.signing
import bitcoin
from hashlib import sha256
from binascii import unhexlify, hexlify
from collections import OrderedDict
from urllib2 import Request, urlopen, URLError

import re
import os
import nacl.encoding
from twisted.internet import reactor
from protos.objects import Listings
from protos.countries import CountryCode
from dht.utils import digest
from constants import DATA_FOLDER
from market.profile import Profile
from keyutils.keys import KeyChain
from keyutils.bip32utils import derive_childkey
from log import Logger


class Contract(object):
    """
    A class for creating and interacting with OpenBazaar Ricardian contracts.
    """

    def __init__(self, database, contract=None, hash_value=None, testnet=False):
        """
        This class can be instantiated with either an `OrderedDict` or a hash
        of a contract. If a hash is used, we will load the contract from either
        the file system or cache.

        Alternatively, pass in no parameters if the intent is to create a new
        contract.

        Args:
            contract: an `OrderedDict` containing a filled out json contract
            hash: a hash160 (in raw bytes) of a contract
            testnet: is this contract on the testnet
        """
        self.db = database
        self.keychain = KeyChain(self.db)
        if contract is not None:
            self.contract = contract
        elif hash_value is not None:
            try:
                file_path = self.db.HashMap().get_file(hash_value)
                if file_path is None:
                    file_path = DATA_FOLDER + "cache/" + hexlify(hash_value)
                with open(file_path, 'r') as filename:
                    self.contract = json.load(filename, object_pairs_hook=OrderedDict)
            except Exception:
                try:
                    file_path = DATA_FOLDER + "purchases/in progress/" + hexlify(hash_value) + ".json"
                    with open(file_path, 'r') as filename:
                        self.contract = json.load(filename, object_pairs_hook=OrderedDict)
                except Exception:
                    self.contract = {}
        else:
            self.contract = {}
        self.log = Logger(system=self)

        # used when purchasing this contract
        self.testnet = testnet
        self.ws = None
        self.blockchain = None
        self.amount_funded = 0
        self.received_txs = []
        self.timeout = None
        self.is_purchase = False

    def create(self,
               expiration_date,
               metadata_category,
               title,
               description,
               currency_code,
               price,
               process_time,
               nsfw,
               shipping_origin=None,
               shipping_regions=None,
               est_delivery_domestic=None,
               est_delivery_international=None,
               terms_conditions=None,
               returns=None,
               keywords=None,
               category=None,
               condition=None,
               sku=None,
               images=None,
               free_shipping=None,
               shipping_currency_code=None,
               shipping_domestic=None,
               shipping_international=None,
               options=None,
               moderators=None):
        """
        All parameters are strings except:

        :param expiration_date: `string` (must be formatted UTC datetime)
        :param keywords: `list`
        :param nsfw: `boolean`
        :param images: a `list` of image files
        :param free_shipping: `boolean`
        :param shipping_origin: a 'string' formatted `CountryCode`
        :param shipping_regions: a 'list' of 'string' formatted `CountryCode`s
        :param options: a 'dict' containing options as keys and 'list' as option values.
        :param moderators: a 'list' of 'string' guids (hex encoded).
        """

        profile = Profile(self.db).get()
        self.contract = OrderedDict(
            {
                "vendor_offer": {
                    "listing": {
                        "metadata": {
                            "version": "0.1",
                            "category": metadata_category.lower(),
                            "category_sub": "fixed price"
                        },
                        "id": {
                            "guid": self.keychain.guid.encode("hex"),
                            "pubkeys": {
                                "guid": self.keychain.guid_signed_pubkey[64:].encode("hex"),
                                "bitcoin": bitcoin.bip32_extract_key(self.keychain.bitcoin_master_pubkey),
                                "encryption": self.keychain.encryption_pubkey.encode("hex")
                            }
                        },
                        "item": {
                            "title": title,
                            "description": description,
                            "process_time": process_time,
                            "price_per_unit": {},
                            "nsfw": nsfw
                        }
                    }
                }
            }
        )
        if expiration_date.lower() == "never":
            self.contract["vendor_offer"]["listing"]["metadata"]["expiry"] = "never"
        else:
            self.contract["vendor_offer"]["listing"]["metadata"]["expiry"] = expiration_date + " UTC"
        if metadata_category == "physical good" and condition is not None:
            self.contract["vendor_offer"]["listing"]["item"]["condition"] = condition
        if currency_code.upper() == "BTC":
            item = self.contract["vendor_offer"]["listing"]["item"]
            item["price_per_unit"]["bitcoin"] = price
        else:
            item = self.contract["vendor_offer"]["listing"]["item"]
            item["price_per_unit"]["fiat"] = {}
            item["price_per_unit"]["fiat"]["price"] = price
            item["price_per_unit"]["fiat"]["currency_code"] = currency_code
        if keywords is not None:
            self.contract["vendor_offer"]["listing"]["item"]["keywords"] = []
            self.contract["vendor_offer"]["listing"]["item"]["keywords"].extend(keywords)
        if category is not None:
            self.contract["vendor_offer"]["listing"]["item"]["category"] = category
        if sku is not None:
            self.contract["vendor_offer"]["listing"]["item"]["sku"] = sku
        if options is not None:
            self.contract["vendor_offer"]["listing"]["item"]["options"] = options
        if metadata_category == "physical good":
            self.contract["vendor_offer"]["listing"]["shipping"] = {}
            shipping = self.contract["vendor_offer"]["listing"]["shipping"]
            shipping["shipping_origin"] = shipping_origin
            if free_shipping is False:
                self.contract["vendor_offer"]["listing"]["shipping"]["free"] = False
                self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"] = {}
                if shipping_currency_code == "BTC":
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"] = {}
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"][
                        "domestic"] = shipping_domestic
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"][
                        "international"] = shipping_international
                else:
                    shipping = self.contract["vendor_offer"]["listing"]["shipping"]
                    shipping["flat_fee"]["fiat"] = {}
                    shipping["flat_fee"]["fiat"]["price"] = {}
                    shipping["flat_fee"]["fiat"]["price"][
                        "domestic"] = shipping_domestic
                    shipping["flat_fee"]["fiat"]["price"][
                        "international"] = shipping_international
                    shipping["flat_fee"]["fiat"][
                        "currency_code"] = shipping_currency_code
            else:
                self.contract["vendor_offer"]["listing"]["shipping"]["free"] = True
            self.contract["vendor_offer"]["listing"]["shipping"]["shipping_regions"] = []
            for region in shipping_regions:
                shipping = self.contract["vendor_offer"]["listing"]["shipping"]
                shipping["shipping_regions"].append(region)
            listing = self.contract["vendor_offer"]["listing"]
            listing["shipping"]["est_delivery"] = {}
            listing["shipping"]["est_delivery"]["domestic"] = est_delivery_domestic
            listing["shipping"]["est_delivery"][
                "international"] = est_delivery_international
        if profile.HasField("handle"):
            self.contract["vendor_offer"]["listing"]["id"]["blockchain_id"] = profile.handle
        if images is not None:
            self.contract["vendor_offer"]["listing"]["item"]["image_hashes"] = []
            for image_hash in images:
                self.contract["vendor_offer"]["listing"]["item"]["image_hashes"].append(image_hash)
        if terms_conditions is not None or returns is not None:
            self.contract["vendor_offer"]["listing"]["policy"] = {}
            if terms_conditions is not None:
                self.contract["vendor_offer"]["listing"]["policy"]["terms_conditions"] = terms_conditions
            if returns is not None:
                self.contract["vendor_offer"]["listing"]["policy"]["returns"] = returns
        if moderators is not None:
            self.contract["vendor_offer"]["listing"]["moderators"] = []
            for mod in moderators:
                mod_info = self.db.ModeratorStore().get_moderator(unhexlify(mod))
                print mod_info
                if mod_info is not None:
                    moderator = {
                        "guid": mod,
                        "blockchain_id": mod_info[6],
                        "pubkeys": {
                            "signing": {
                                "key": mod_info[1][64:].encode("hex"),
                                "signature": mod_info[1][:64].encode("hex")
                            },
                            "encryption": {
                                "key": mod_info[2].encode("hex"),
                                "signature": mod_info[3].encode("hex")
                            },
                            "bitcoin": {
                                "key": mod_info[4].encode("hex"),
                                "signature": mod_info[5].encode("hex")
                            }
                        }
                    }
                    self.contract["vendor_offer"]["listing"]["moderators"].append(moderator)

        listing = json.dumps(self.contract["vendor_offer"]["listing"], indent=4)
        self.contract["vendor_offer"]["signature"] = \
            self.keychain.signing_key.sign(listing, encoder=nacl.encoding.HexEncoder)[:128]
        self.save()

    def add_purchase_info(self,
                          quantity,
                          ship_to=None,
                          shipping_address=None,
                          city=None,
                          state=None,
                          postal_code=None,
                          country=None,
                          moderator=None,
                          options=None):
        """
        Update the contract with the buyer's purchase information.
        """

        profile = Profile(self.db).get()
        order_json = {
            "buyer_order": {
                "order": {
                    "ref_hash": digest(json.dumps(self.contract, indent=4)).encode("hex"),
                    "quantity": quantity,
                    "id": {
                        "guid": self.keychain.guid.encode("hex"),
                        "pubkeys": {
                            "guid": self.keychain.guid_signed_pubkey[64:].encode("hex"),
                            "bitcoin": bitcoin.bip32_extract_key(self.keychain.bitcoin_master_pubkey),
                            "encryption": self.keychain.encryption_pubkey.encode("hex")
                        }
                    },
                    "payment": {}
                }
            }
        }
        if profile.HasField("handle"):
            order_json["buyer_order"]["order"]["id"]["blockchain_id"] = profile.handle
        if self.contract["vendor_offer"]["listing"]["metadata"]["category"] == "physical good":
            order_json["buyer_order"]["order"]["shipping"] = {}
            order_json["buyer_order"]["order"]["shipping"]["ship_to"] = ship_to
            order_json["buyer_order"]["order"]["shipping"]["address"] = shipping_address
            order_json["buyer_order"]["order"]["shipping"]["city"] = city
            order_json["buyer_order"]["order"]["shipping"]["state"] = state
            order_json["buyer_order"]["order"]["shipping"]["postal_code"] = postal_code
            order_json["buyer_order"]["order"]["shipping"]["country"] = country
        if options is not None:
            order_json["buyer_order"]["order"]["options"] = options
        if moderator:  # TODO: Handle direct payments
            chaincode = sha256(str(random.getrandbits(256))).digest().encode("hex")
            order_json["buyer_order"]["order"]["payment"]["chaincode"] = chaincode
            valid_mod = False
            for mod in self.contract["vendor_offer"]["listing"]["moderators"]:
                if mod["guid"] == moderator:
                    order_json["buyer_order"]["order"]["moderator"] = moderator
                    masterkey_m = mod["pubkeys"]["bitcoin"]["key"]
                    valid_mod = True
            if not valid_mod:
                return False
            masterkey_b = bitcoin.bip32_extract_key(self.keychain.bitcoin_master_pubkey)
            masterkey_v = self.contract["vendor_offer"]["listing"]["id"]["pubkeys"]["bitcoin"]
            buyer_key = derive_childkey(masterkey_b, chaincode)
            vendor_key = derive_childkey(masterkey_v, chaincode)
            moderator_key = derive_childkey(masterkey_m, chaincode)

            redeem_script = '75' + bitcoin.mk_multisig_script([buyer_key, vendor_key, moderator_key], 2)
            order_json["buyer_order"]["order"]["payment"]["redeem_script"] = redeem_script
            if self.testnet:
                payment_address = bitcoin.p2sh_scriptaddr(redeem_script, 196)
            else:
                payment_address = bitcoin.p2sh_scriptaddr(redeem_script)
            order_json["buyer_order"]["order"]["payment"]["address"] = payment_address

        price_json = self.contract["vendor_offer"]["listing"]["item"]["price_per_unit"]
        if "bitcoin" in price_json:
            order_json["buyer_order"]["order"]["payment"]["amount"] = price_json["bitcoin"]
        else:
            currency_code = price_json["fiat"]["currency_code"]
            fiat_price = price_json["fiat"]["price"]
            try:
                request = Request('https://api.bitcoinaverage.com/ticker/' + currency_code.upper() + '/last')
                response = urlopen(request)
                conversion_rate = response.read()
            except URLError:
                return False
            order_json["buyer_order"]["order"]["payment"]["amount"] = float(
                "{0:.8f}".format(float(fiat_price) / float(conversion_rate)))

        self.contract["buyer_order"] = order_json["buyer_order"]
        order = json.dumps(self.contract["buyer_order"]["order"], indent=4)
        self.contract["buyer_order"]["signature"] = \
            self.keychain.signing_key.sign(order, encoder=nacl.encoding.HexEncoder)[:128]

        return self.contract["buyer_order"]["order"]["payment"]["address"]

    def add_order_confirmation(self,
                               payout_address,
                               comments=None,
                               shipper=None,
                               tracking_number=None,
                               est_delivery=None,
                               url=None,
                               password=None):
        """
        Add the vendor's order confirmation to the contract.
        """

        if not self.testnet and not (payout_address[:1] == "1" or payout_address[:1] == "3"):
            raise Exception("Bitcoin address is not a mainnet address")
        elif self.testnet and not \
                (payout_address[:1] == "n" or payout_address[:1] == "m" or payout_address[:1] == "2"):
            raise Exception("Bitcoin address is not a testnet address")
        try:
            bitcoin.b58check_to_hex(payout_address)
        except AssertionError:
            raise Exception("Invalid Bitcoin address")
        conf_json = {
            "vendor_order_confirmation": {
                "invoice": {
                    "ref_hash": digest(json.dumps(self.contract, indent=4)).encode("hex"),
                    "payout_address": payout_address
                }
            }
        }
        if self.contract["vendor_offer"]["listing"]["metadata"]["category"] == "physical good":
            shipping = {"shipper": shipper, "tracking_number": tracking_number, "est_delivery": est_delivery}
            conf_json["vendor_order_confirmation"]["invoice"]["shipping"] = shipping
        elif self.contract["vendor_offer"]["listing"]["metadata"]["category"] == "digital good":
            content_source = {"url": url, "password": password}
            conf_json["vendor_order_confirmation"]["invoice"]["content_source"] = content_source
        if comments:
            conf_json["vendor_order_confirmation"]["invoice"]["comments"] = comments
        confirmation = json.dumps(conf_json["vendor_order_confirmation"]["invoice"], indent=4)
        conf_json["vendor_order_confirmation"]["signature"] = \
            self.keychain.signing_key.sign(confirmation, encoder=nacl.encoding.HexEncoder)[:128]
        order_id = digest(json.dumps(self.contract, indent=4)).encode("hex")
        self.contract["vendor_order_confirmation"] = conf_json["vendor_order_confirmation"]
        self.db.Sales().update_status(order_id, 2)
        file_path = DATA_FOLDER + "store/listings/in progress/" + order_id + ".json"
        with open(file_path, 'w') as outfile:
            outfile.write(json.dumps(self.contract, indent=4))

    def accept_order_confirmation(self, ws, confirmation_json=None):
        """
        Validate the order confirmation sent over from the seller and update our node accordingly.
        """
        self.ws = ws
        try:
            if confirmation_json:
                self.contract["vendor_order_confirmation"] = json.loads(confirmation_json,
                                                                        object_pairs_hook=OrderedDict)

            contract_dict = json.loads(json.dumps(self.contract, indent=4), object_pairs_hook=OrderedDict)
            del contract_dict["vendor_order_confirmation"]
            contract_hash = digest(json.dumps(contract_dict, indent=4)).encode("hex")
            ref_hash = self.contract["vendor_order_confirmation"]["invoice"]["ref_hash"]
            if ref_hash != contract_hash:
                raise Exception("Order number doesn't match")
            if self.contract["vendor_offer"]["listing"]["metadata"]["category"] == "physical good":
                shipping = self.contract["vendor_order_confirmation"]["invoice"]["shipping"]
                if "tracking_number" not in shipping or "shipper" not in shipping:
                    raise Exception("No shipping information")
            # update the order status in the db
            self.db.Purchases().update_status(contract_hash, 2)
            file_path = DATA_FOLDER + "purchases/in progress/" + contract_hash + ".json"

            # update the contract in the file system
            with open(file_path, 'w') as outfile:
                outfile.write(json.dumps(self.contract, indent=4))
            message_json = {
                "order_confirmation": {
                    "order_id": contract_hash,
                    "title": self.contract["vendor_offer"]["listing"]["item"]["title"]
                }
            }
            # push the message over websockets
            self.ws.push(json.dumps(message_json, indent=4))
            return contract_hash
        except Exception:
            return False

    def await_funding(self, websocket_server, libbitcoin_client, proofSig, is_purchase=True):
        """
        Saves the contract to the file system and db as an unfunded contract.
        Listens on the libbitcoin server for the multisig address to be funded.
        Deletes the unfunded contract from the file system and db if it goes
        unfunded for more than 10 minutes.
        """

        # TODO: Handle direct payments
        self.ws = websocket_server
        self.blockchain = libbitcoin_client
        self.is_purchase = is_purchase
        order_id = digest(json.dumps(self.contract, indent=4)).encode("hex")
        payment_address = self.contract["buyer_order"]["order"]["payment"]["address"]
        vendor_item = self.contract["vendor_offer"]["listing"]["item"]
        if "image_hashes" in vendor_item:
            thumbnail_hash = vendor_item["image_hashes"][0]
        else:
            thumbnail_hash = ""
        if "blockchain_id" in self.contract["vendor_offer"]["listing"]["id"]:
            vendor = self.contract["vendor_offer"]["listing"]["id"]["blockchain_id"]
        else:
            vendor = self.contract["vendor_offer"]["listing"]["id"]["guid"]
        if is_purchase:
            file_path = DATA_FOLDER + "purchases/in progress/" + order_id + ".json"
            self.db.Purchases().new_purchase(order_id,
                                             self.contract["vendor_offer"]["listing"]["item"]["title"],
                                             time.time(),
                                             self.contract["buyer_order"]["order"]["payment"]["amount"],
                                             payment_address,
                                             0,
                                             thumbnail_hash,
                                             vendor,
                                             proofSig)
        else:
            file_path = DATA_FOLDER + "store/listings/in progress/" + order_id + ".json"
            self.db.Sales().new_sale(order_id,
                                     self.contract["vendor_offer"]["listing"]["item"]["title"],
                                     time.time(),
                                     self.contract["buyer_order"]["order"]["payment"]["amount"],
                                     payment_address,
                                     0,
                                     thumbnail_hash,
                                     vendor)

        with open(file_path, 'w') as outfile:
            outfile.write(json.dumps(self.contract, indent=4))
        self.timeout = reactor.callLater(600, self._delete_unfunded)
        self.blockchain.subscribe_address(payment_address, notification_cb=self.on_tx_received)

    def _delete_unfunded(self):
        """
        The user failed to fund the contract in the 10 minute window. Remove it from
        the file system and db.
        """

        order_id = digest(json.dumps(self.contract, indent=4)).encode("hex")
        if self.is_purchase:
            file_path = DATA_FOLDER + "purchases/in progress/" + order_id + ".json"
            self.db.Purchases().delete_purchase(order_id)
        else:
            file_path = DATA_FOLDER + "store/listings/in progress/" + order_id + ".json"
            self.db.Sales().delete_sale(order_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    def on_tx_received(self, address_version, address_hash, height, block_hash, tx):
        """
        Fire when the libbitcoin server tells us we received a payment to this funding address.
        While unlikely, a user may send multiple transactions to the funding address reach the
        funding level. We need to keep a running balance and increment it when a new transaction
        is received. If the contract is fully funded, we push a notification to the websockets.
        """

        # decode the transaction
        transaction = bitcoin.deserialize(tx.encode("hex"))

        # get the amount (in satoshi) the user is expected to pay
        amount_to_pay = int(float(self.contract["buyer_order"]["order"]["payment"]["amount"]) * 100000000)
        if tx not in self.received_txs:  # make sure we aren't parsing the same tx twice.
            output_script = 'a914' + digest(unhexlify(
                self.contract["buyer_order"]["order"]["payment"]["redeem_script"])).encode("hex") + '87'
            for output in transaction["outs"]:
                if output["script"] == output_script:
                    self.amount_funded += output["value"]
                    if tx not in self.received_txs:
                        self.received_txs.append(tx)
            if self.amount_funded >= amount_to_pay:  # if fully funded
                self.timeout.cancel()
                self.blockchain.unsubscribe_address(
                    self.contract["buyer_order"]["order"]["payment"]["address"], self.on_tx_received)
                order_id = digest(json.dumps(self.contract, indent=4)).encode("hex")
                if self.is_purchase:
                    message_json = {
                        "payment_received": {
                            "address": self.contract["buyer_order"]["order"]["payment"]["address"],
                            "order_id": order_id
                            }
                    }

                    # update the db
                    self.db.Purchases().update_status(order_id, 1)
                    self.log.info("Payment for order id %s successfully broadcast to network." % order_id)
                else:
                    message_json = {
                        "new_order": {
                            "order_id": order_id,
                            "title": self.contract["vendor_offer"]["listing"]["item"]["title"]
                            }
                    }
                    self.db.Sales().update_status(order_id, 1)
                    self.log.info("Received new order %s" % order_id)

                # push the message over websockets
                self.ws.push(json.dumps(message_json, indent=4))

    def get_contract_id(self):
        contract = json.dumps(self.contract, indent=4)
        return digest(contract)

    def delete(self, delete_images=True):
        """
        Deletes the contract json from the OpenBazaar directory as well as the listing
        metadata from the db and all the related images in the file system.
        """

        # build the file_name from the contract
        file_name = str(self.contract["vendor_offer"]["listing"]["item"]["title"][:100])
        file_name = re.sub(r"[^\w\s]", '', file_name)
        file_name = re.sub(r"\s+", '_', file_name)
        file_path = DATA_FOLDER + "store/listings/contracts/" + file_name + ".json"

        h = self.db.HashMap()

        # maybe delete the images from disk
        if "image_hashes" in self.contract["vendor_offer"]["listing"]["item"] and delete_images:
            for image_hash in self.contract["vendor_offer"]["listing"]["item"]["image_hashes"]:
                # delete from disk
                image_path = h.get_file(unhexlify(image_hash))
                if os.path.exists(image_path):
                    os.remove(image_path)
                # remove pointer to the image from the HashMap
                h.delete(unhexlify(image_hash))

        # delete the contract from disk
        if os.path.exists(file_path):
            os.remove(file_path)

        # delete the listing metadata from the db
        contract_hash = digest(json.dumps(self.contract, indent=4))
        self.db.ListingsStore().delete_listing(contract_hash)

        # remove the pointer to the contract from the HashMap
        h.delete(contract_hash)

    def save(self):
        """
        Saves the json contract into the OpenBazaar/store/listings/contracts/ directory.
        It uses the title as the file name so it's easy on human eyes. A mapping of the
        hash of the contract and file path is stored in the database so we can retrieve
        the contract with only its hash.

        Additionally, the contract metadata (sent in response to the GET_LISTINGS query)
        is saved in the db for fast access.
        """

        # get the contract title to use as the file name and format it
        file_name = str(self.contract["vendor_offer"]["listing"]["item"]["title"][:100])
        file_name = re.sub(r"[^\w\s]", '', file_name)
        file_name = re.sub(r"\s+", '_', file_name)

        # save the json contract to the file system
        file_path = DATA_FOLDER + "store/listings/contracts/" + file_name + ".json"
        with open(file_path, 'w') as outfile:
            outfile.write(json.dumps(self.contract, indent=4))

        # Create a `ListingMetadata` protobuf object using data from the full contract
        listings = Listings()
        data = listings.ListingMetadata()
        data.contract_hash = digest(json.dumps(self.contract, indent=4))
        vendor_item = self.contract["vendor_offer"]["listing"]["item"]
        data.title = vendor_item["title"]
        if "image_hashes" in vendor_item:
            data.thumbnail_hash = unhexlify(vendor_item["image_hashes"][0])
        if "category" in vendor_item:
            data.category = vendor_item["category"]
        if "bitcoin" not in vendor_item["price_per_unit"]:
            data.price = float(vendor_item["price_per_unit"]["fiat"]["price"])
            data.currency_code = vendor_item["price_per_unit"]["fiat"][
                "currency_code"]
        else:
            data.price = float(vendor_item["price_per_unit"]["bitcoin"])
            data.currency_code = "BTC"
        data.nsfw = vendor_item["nsfw"]
        if "shipping" not in self.contract["vendor_offer"]["listing"]:
            data.origin = CountryCode.Value("NA")
        else:
            data.origin = CountryCode.Value(
                self.contract["vendor_offer"]["listing"]["shipping"]["shipping_origin"].upper())
            for region in self.contract["vendor_offer"]["listing"]["shipping"]["shipping_regions"]:
                data.ships_to.append(CountryCode.Value(region.upper()))

        # save the mapping of the contract file path and contract hash in the database
        self.db.HashMap().insert(data.contract_hash, file_path)

        # save the `ListingMetadata` protobuf to the database as well
        self.db.ListingsStore().add_listing(data)

    def verify(self, sender_key):
        """
        Validate that an order sent over by a buyer is filled out correctly.
        """

        try:
            contract_dict = json.loads(json.dumps(self.contract, indent=4), object_pairs_hook=OrderedDict)
            del contract_dict["buyer_order"]
            contract_hash = digest(json.dumps(contract_dict, indent=4))

            ref_hash = unhexlify(self.contract["buyer_order"]["order"]["ref_hash"])

            # verify that the reference hash matches the contract and that the contract actually exists
            if contract_hash != ref_hash or not self.db.HashMap().get_file(ref_hash):
                raise Exception("Order for contract that doesn't exist")

            # verify the signature on the order
            verify_key = nacl.signing.VerifyKey(sender_key)
            verify_key.verify(json.dumps(self.contract["buyer_order"]["order"], indent=4),
                              unhexlify(self.contract["buyer_order"]["signature"]))

            # verify buyer included the correct bitcoin amount for payment
            price_json = self.contract["vendor_offer"]["listing"]["item"]["price_per_unit"]
            if "bitcoin" in price_json:
                asking_price = price_json["bitcoin"]
            else:
                currency_code = price_json["fiat"]["currency_code"]
                fiat_price = price_json["fiat"]["price"]
                request = Request('https://api.bitcoinaverage.com/ticker/' + currency_code.upper() + '/last')
                response = urlopen(request)
                conversion_rate = response.read()
                asking_price = float("{0:.8f}".format(float(fiat_price) / float(conversion_rate)))
            if asking_price > self.contract["buyer_order"]["order"]["payment"]["amount"]:
                raise Exception("Insuffient Payment")

            # verify a valid moderator was selected
            # TODO: handle direct payments
            valid_mod = False
            for mod in self.contract["vendor_offer"]["listing"]["moderators"]:
                if mod["guid"] == self.contract["buyer_order"]["order"]["moderator"]:
                    valid_mod = True
            if not valid_mod:
                raise Exception("Invalid moderator")

            # verify all the shipping fields exist
            if self.contract["vendor_offer"]["listing"]["metadata"]["category"] == "physical good":
                shipping = self.contract["buyer_order"]["order"]["shipping"]
                keys = ["ship_to", "address", "postal_code", "city", "state", "country"]
                for value in map(shipping.get, keys):
                    if value is None:
                        raise Exception("Missing shipping field")

            # verify buyer ID
            pubkeys = self.contract["buyer_order"]["order"]["id"]["pubkeys"]
            keys = ["guid", "bitcoin", "encryption"]
            for value in map(pubkeys.get, keys):
                if value is None:
                    raise Exception("Missing pubkey field")

            # verify redeem script
            chaincode = self.contract["buyer_order"]["order"]["payment"]["chaincode"]
            for mod in self.contract["vendor_offer"]["listing"]["moderators"]:
                if mod["guid"] == self.contract["buyer_order"]["order"]["moderator"]:
                    masterkey_m = mod["pubkeys"]["bitcoin"]["key"]

            masterkey_v = bitcoin.bip32_extract_key(self.keychain.bitcoin_master_pubkey)
            masterkey_b = self.contract["buyer_order"]["order"]["id"]["pubkeys"]["bitcoin"]
            buyer_key = derive_childkey(masterkey_b, chaincode)
            vendor_key = derive_childkey(masterkey_v, chaincode)
            moderator_key = derive_childkey(masterkey_m, chaincode)

            redeem_script = '75' + bitcoin.mk_multisig_script([buyer_key, vendor_key, moderator_key], 2)
            if redeem_script != self.contract["buyer_order"]["order"]["payment"]["redeem_script"]:
                raise Exception("Invalid redeem script")

            # verify the payment address
            if self.testnet:
                payment_address = bitcoin.p2sh_scriptaddr(redeem_script, 196)
            else:
                payment_address = bitcoin.p2sh_scriptaddr(redeem_script)
            if payment_address != self.contract["buyer_order"]["order"]["payment"]["address"]:
                raise Exception("Incorrect payment address")

            return True

        except Exception:
            return False
