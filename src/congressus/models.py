from datetime import date as Date
from datetime import datetime as DateTime
from typing import Literal

from pydantic import BaseModel


class Locale(BaseModel):
    code: str
    id: int
    name: str


class Country(BaseModel):
    calling_code: str
    country_code: str
    default_locale: Locale
    id: int
    name: str
    name_local: str
    name_locale_en: str
    name_locale_nl: str


class Address(BaseModel):
    address: str | None = None
    city: str | None = None
    country: Country
    lat: float | None = None
    lng: float | None = None
    location: str | None = None
    province: str | None = None
    zip: str | None = None


class StorageFolder(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    path: str
    breadcrumbs: str
    published: bool


class Folder(BaseModel):
    breadcrumbs: str
    id: int
    name: str
    order_type: str
    parent_id: int
    path: str
    published: bool
    slug: str


class Phone(BaseModel):
    number: str
    number_full: str
    number_full_MSISDN: str
    number_formatted: str
    country: Country


class StorageObject(BaseModel):
    id: int
    url: str | None = None
    url_sm: str | None = None
    url_md: str | None = None
    url_lg: str | None = None
    is_image: bool | None = None
    type: Literal["members", "files", "template", "groups", "user", "gallery", "contracts"] | None = None
    filename: str | None = None
    name: str | None = None
    size: int
    extension: str
    content_type: str
    image_width: int | None = None
    image_height: int | None = None
    folder: StorageFolder | None = None


class GroupMembership(BaseModel):
    id: int
    member_id: int
    start: Date | None = None
    end: Date | None = None
    function: str | None = None
    may_edit_profile: bool
    may_manage_memberships: bool
    may_manage_storage_objects: bool
    is_self_enroll: bool
    order_type: str
    order: int
    group_id: int
    group: "Group"


class Group(BaseModel):
    address: Address
    description: str | None = None
    description_short: str | None = None
    email: str | None = None
    end: Date | None = None
    folder: Folder
    folder_id: int
    id: int
    logo: StorageObject | None = None
    memberships: list[GroupMembership]
    memo: str
    name: str
    path: str
    phone: str | None = None
    postal_address: str | None = None
    published: bool
    slug: str
    start: Date | None = None
    url: str | None = None


GroupMembership.model_rebuild()


class MemberStatus(BaseModel):
    id: int
    name: str
    status_id: int
    member_from: Date
    member_to: Date | None = None
    archived: bool
    deceased: bool


class SddMandate(BaseModel):
    entity_id: int
    entity_name: str
    reference: str | None = None
    date: Date | None = None
    date_cancelled: Date | None = None
    is_valid: bool


class BankAccount(BaseModel):
    iban: str | None = None
    bic: str | None = None
    iban_formatted: str | None = None
    iban_masked: str | None = None
    sdd_mandates: list[SddMandate] | None = None


class Member(BaseModel):
    id: int
    username: str
    status: MemberStatus
    statuses: list[MemberStatus]
    gender: Literal["m", "f", "o", ""] | None = None
    prefix: str | None = None
    initials: str | None = None
    nickname: str | None = None
    given_name: str | None = None
    first_name: str | None = None
    primary_last_name_main: str | None = None
    primary_last_name_prefix: str | None = None
    primary_last_name: str
    secondary_last_name_main: str | None = None
    secondary_last_name_prefix: str | None = None
    secondary_last_name: str | None = None
    last_name_display: str | None = None
    last_name: str
    search_name: str | None = None
    suffix: str | None = None
    date_of_birth: Date | None = None
    email: str | None = None
    phone_mobile: Phone | None = None
    phone_home: Phone | None = None
    address: Address | None = None
    profile_picture_id: int | None = None
    profile_picture: StorageObject | None = None
    formal_picture_id: int | None = None
    formal_picture: StorageObject | None = None
    deleted: bool | None = None
    receive_sms: bool
    receive_mailings: bool
    locked: bool
    show_almanac: bool
    show_almanac_addresses: bool
    show_almanac_phonenumbers: bool
    show_almanac_email: bool
    show_almanac_date_of_birth: bool
    show_almanac_custom_fields: bool
    modified: DateTime | None = None
    bank_account: BankAccount | None = None
    custom_field_data: dict
