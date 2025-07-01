from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class Url(BaseModel):
    x_id: Optional[str]
    url: Optional[str]
    valid: Optional[bool]


class Copyright(BaseModel):
    value: Optional[str] = None
    valueFormat: Optional[str] = None


class FormCopyright(BaseModel):
    authority: Optional[str] = None
    valueFormat: Optional[str] = None
    urls: Optional[List[Url]] = None


class Source(BaseModel):
    sourceName: Optional[str]
    created: Optional[str] = None
    updated: Optional[str] = None
    registrationStatus: Optional[str] = None
    datatype: Optional[str] = None
    copyright: Optional[Copyright] = None


class CreatedBy(BaseModel):
    username: Optional[str]


class UpdatedBy(BaseModel):
    username: Optional[str]


class StewardOrg(BaseModel):
    name: Optional[str]


class ReplacedBy(BaseModel):
    tinyId: Optional[str]


class MergedTo(BaseModel):
    tinyId: Optional[str]


class RegistrationState(BaseModel):
    administrativeNote: Optional[str] = None
    administrativeStatus: Optional[str] = None
    effectiveDate: Optional[str] = None
    registrationStatus: Optional[str]
    replacedBy: Optional[ReplacedBy] = None
    mergedTo: Optional[MergedTo] = None
    unresolvedIssue: Optional[str] = None
    untilDate: Optional[str] = None


class Tag(BaseModel):
    tag: Optional[str]


class Designation(BaseModel):
    designation: Optional[str]
    sources: Optional[List[str]]
    tags: Optional[List[str]]


class Definition(BaseModel):
    definition: Optional[str]
    definitionFormat: Optional[str] = None
    sources: Optional[List[str]] = None
    tags: Optional[List[str]]


class DatatypeDate(BaseModel):
    format: Optional[str] = None


class DatatypeDynamicCodeList(BaseModel):
    system: Optional[str]


class DatatypeExternallyDefined(BaseModel):
    description: Optional[str] = None
    descriptionFormat: Optional[str] = None
    link: Optional[str] = None


class DatatypeNumber(BaseModel):
    maxValue: Optional[Union[float, int]] = None
    minValue: Optional[Union[float, int]] = None
    precision: Optional[int] = None


class DatatypeText(BaseModel):
    maxLength: Optional[int] = None
    minLength: Optional[int] = None
    regex: Optional[str] = None
    rule: Optional[str] = None


class DatatypeTime(BaseModel):
    format: Optional[str]


class DatatypeValueList(BaseModel):
    datatype: Optional[str]


class Identifier(BaseModel):
    id: Optional[str]
    source: Optional[str]
    version: Optional[str] = None


class PermissibleValue(BaseModel):
    codeSystemName: Optional[str] = None
    codeSystemVersion: Optional[str] = None
    permissibleValue: Optional[str]
    valueMeaningCode: Optional[str] = None
    valueMeaningDefinition: Optional[str] = None
    valueMeaningName: Optional[str] = None
    conceptId: Optional[str] = None
    conceptSource: Optional[str] = None


class ValueDomain(BaseModel):
    datatype: Optional[str]
    datatypeDate: Optional[DatatypeDate] = None
    datatypeDynamicCodeList: Optional[DatatypeDynamicCodeList] = None
    datatypeExternallyDefined: Optional[DatatypeExternallyDefined] = None
    datatypeNumber: Optional[DatatypeNumber] = None
    datatypeText: Optional[DatatypeText] = None
    datatypeTime: Optional[DatatypeTime] = None
    datatypeValueList: Optional[DatatypeValueList] = None
    definition: Optional[str] = None
    identifiers: Optional[List[Identifier]]
    ids: Optional[List[Identifier]]
    name: Optional[str] = None
    permissibleValues: Optional[List[PermissibleValue]]
    uom: Optional[str] = None
    vsacOid: Optional[str] = None


class ElementInner(BaseModel):
    elements: Optional[List[Optional[dict]]]
    name: Optional[str]


class Classification(BaseModel):
    elements: Optional[List[ElementInner]]
    stewardOrg: Optional[StewardOrg]
    workingGroup: Optional[bool] = None


class ReferenceDocument(BaseModel):
    document: Optional[str] = None
    docType: Optional[str] = None
    languageCode: Optional[str] = None
    providerOrg: Optional[str] = None
    referenceDocumentId: Optional[str] = None
    source: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    uri: Optional[str] = None


class Property(BaseModel):
    key: Optional[str]
    source: Optional[str] = None
    value: Optional[str]
    valueFormat: Optional[str] = None


class UploadedBy(BaseModel):
    username: Optional[str]


class Attachment(BaseModel):
    comment: Optional[str] = None
    fileid: Optional[str] = None
    filename: Optional[str] = None
    filesize: Optional[int] = None
    filetype: Optional[str] = None
    isDefault: Optional[bool] = None
    pendingApproval: Optional[bool] = None
    scanned: Optional[bool] = None
    uploadedBy: Optional[UploadedBy] = None
    uploadDate: Optional[str] = None


class Reply(BaseModel):
    created: Optional[str]
    pendingApproval: Optional[bool]
    status: Optional[str]
    text: Optional[str]
    user: Optional[str]
    usename: Optional[str]


class Element(BaseModel):
    eltId: Optional[str]
    eltType: Optional[str]


class Comment(BaseModel):
    created: Optional[str]
    element: Optional[Element]
    linkedTab: Optional[str]
    pendingApproval: Optional[bool]
    replies: Optional[List[Reply]]
    status: Optional[str]
    text: Optional[str]
    user: Optional[str]
    usename: Optional[str]


class DataSet(BaseModel):
    id: Optional[str] = None
    notes: Optional[str]
    source: Optional[str]
    studyUri: Optional[str]


class DerivationRule(BaseModel):
    formula: Optional[str]
    inputs: Optional[List[str]]
    name: Optional[str]
    outputs: Optional[List[str]]
    ruleType: Optional[str]


class ClassificationScheme(BaseModel):
    id: Optional[str]
    preferredName: Optional[str]
    longName: Optional[str]


class Protocol(BaseModel):
    id: Optional[str]
    preferredName: Optional[str]
    longName: Optional[str]


class Context(BaseModel):
    id: Optional[str]
    name: Optional[str]


class DisplayProfile(BaseModel):
    displayInstructions: Optional[bool] = None
    displayInvisible: Optional[bool] = None
    displayNumbering: Optional[bool] = None
    displayType: Optional[str]
    displayValues: Optional[bool] = None
    name: Optional[str] = None
    numberOfColumns: Optional[int] = None
    repeatFormat: Optional[str] = None
    sectionsAsMatrix: Optional[bool] = None


class Instruction(BaseModel):
    value: Optional[str] = None
    valueFormat: Optional[str] = None


class Form(BaseModel):
    name: Optional[str] = None
    tinyID: Optional[str] = None
    version: Optional[str] = None


class InForm(BaseModel):
    form: Optional[Form] = None


class NewCde(BaseModel):
    definitions: Optional[List[Definition]] = None
    designations: Optional[List[Designation]] = None
    x_id: Optional[str] = None  # Field(alias="x_id", default=None)


class CDE(BaseModel):
    ids: Optional[List[Identifier]]
    newCde: Optional[NewCde] = None
    name: Optional[str] = None
    permissibleValues: Optional[List[PermissibleValue]]
    tinyId: Optional[str] = None
    version: Optional[str] = None


class UnitOfMeasure(BaseModel):
    code: Optional[str]
    system: Optional[str] = None


class Question(BaseModel):
    answers: Optional[List[PermissibleValue]] = None
    cde: Optional[CDE] = None
    datatype: Optional[str] = None
    datatypeDynamicCodeList: Optional[DatatypeDynamicCodeList] = None
    datatypeNumber: Optional[DatatypeNumber] = None
    datatypeText: Optional[DatatypeText] = None
    defaultAnswer: Optional[str] = None
    editable: Optional[bool]
    invisible: Optional[bool]
    multisect: Optional[bool] = None
    required: Optional[bool] = None
    unitsOfMeasure: Optional[List[UnitOfMeasure]]


class SkipLogic(BaseModel):
    action: Optional[str] = None
    condition: Optional[str]


class UndefinedDictModel(BaseModel):
    section: Dict[str, Any]


class FormElement(BaseModel):
    elementType: Optional[str]
    formElements: Optional[List["FormElement"]]
    instructions: Optional[Instruction] = None
    inForm: Optional[InForm] = None
    label: Optional[str] = None
    question: Optional[Question] = None
    repeat: Optional[str] = None
    section: Optional[Dict[str, Any]] = None
    skipLogic: Optional[SkipLogic] = None
