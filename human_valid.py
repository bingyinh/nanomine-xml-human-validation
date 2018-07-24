from lxml import etree as ET
import glob
import collections
import uuid
import csv
import copy

# initialization
def init(xmlsDir):
    xmls = glob.glob(xmlsDir+'*.xml')
    if len(xmls) == 0:
        print 'No xml file found in the directory!'
        return
    IDs_xmls = []
    # loop thru xmls twice, first time get the ID's, second time get other infos
    for xml in xmls:
        tree = ET.parse(xml)
        IDele = tree.find('.//ID')
        if IDele is None:
            ID = str(uuid.uuid4()) + '_S0' # add '_S0' to avoid errors in sort()
        else:
            ID = IDele.text.strip()
        IDs_xmls.append((xml,collections.OrderedDict({'sample ID':ID})))
    # sort IDs_xmls for user's ease, here we assume the ID's follow the naming
    # rule where sample ID S1, S2, etc. indicates the in-group order
    IDs_xmls.sort(key=lambda x: int(x[1]['sample ID'].split('_S')[1].split('_')[0]))
    # copy the list and generate a list with a blank OrderedDict for other fields
    others_xmls = []
    for xmltup in IDs_xmls:
        others_xmls.append((xmltup[0], collections.OrderedDict()))
    # output dict init
    output = collections.OrderedDict(IDs_xmls) # output dict init
    # IDS dict init
    IDS = collections.OrderedDict(copy.deepcopy(IDs_xmls))
    # other blank dict init
    DAT = collections.OrderedDict(copy.deepcopy(others_xmls))
    MAT = collections.OrderedDict(copy.deepcopy(others_xmls))
    PROC = collections.OrderedDict(copy.deepcopy(others_xmls))
    CHAR = collections.OrderedDict(copy.deepcopy(others_xmls))
    PROP = collections.OrderedDict(copy.deepcopy(others_xmls))
    MIC = collections.OrderedDict(copy.deepcopy(others_xmls))
    return xmls, output, IDS, DAT, MAT, PROC, CHAR, PROP, MIC

# generate the dict of infos contained in the xml
def xml_human_valid(xmlsDir, brief):
    xmls, output, IDS, DAT, MAT, PROC, CHAR, PROP, MIC = init(xmlsDir)
    # second loop on xmls
    for xml in xmls:
        tree = ET.parse(xml)
        if brief:
            # Control ID
            output[xml] = extractDetXpath(tree.findall('.//Control_ID'),
                                          output[xml], 'Control ID', '')
            IDS[xml] = extractDetXpath(tree.findall('.//Control_ID'),
                                       IDS[xml], 'Control ID', tree)
            # matrix name
            output[xml] = extractDetXpath(tree.findall('.//MatrixComponent/ChemicalName'),
                                          output[xml], 'Matrix', '')
            MAT[xml] = extractDetXpath(tree.findall('.//MatrixComponent/ChemicalName'),
                                       MAT[xml], 'Matrix', tree)
            # filler name
            output[xml] = extractDetXpath(tree.findall('.//FillerComponent/ChemicalName'),
                                          output[xml], 'Filler', '')
            MAT[xml] = extractDetXpath(tree.findall('.//FillerComponent/ChemicalName'),
                                       MAT[xml], 'Filler', tree)
            # mass volume fraction
            # find parent elements of all Fraction tag
            Fra_pars = tree.findall('.//Fraction/..')
            for Fra_par in Fra_pars:
                prefix = '' # prefix as a header in the output file
                # append the tag of Fra_par to the prefix, could be:
                # MatrixComponentComposition, FillerComposition, and PST_Composition
                prefix += Fra_par.tag
                # based on the schema, only one Fraction is allowed
                Fra = Fra_par.find('Fraction')
                if len(Fra) != 1: # Fraction should only have one child
                    print '%s should only have one child element in node %s/Fraction' %(xml, prefix)
                    continue
                mfvf = Fra[0] # could be mass element or volume element
                prefix += '-' + mfvf.tag
                output[xml][prefix] = mfvf.text
                MAT[xml][prefix] = (mfvf.text, idXpath(tree.getelementpath(mfvf)))
            # PROPERTIES
            root = tree.getroot()
            for ele in root.iter():
                xpath = tree.getelementpath(ele)
                if 'PROPERTIES' not in xpath or '/data' in xpath :
                    continue
                if ele.tag in ['value', 'unit', 'description', 'type']:
                    continue
                children = extractChildren(ele)
                if 'value' in children or 'unit' in children:
                    extractVUDXpath(ele, output[xml], '')
                    extractVUDXpath(ele, PROP[xml], idXpath(xpath))
                if ele.text is not None:
                    # determine the prefix
                    prefix = ele.tag
                    suffix = ''
                    if prefix in output[xml]:
                        ct = 0
                        while ' - '.join([prefix, str(ct)]) in output[xml]:
                            ct += 1
                        suffix = ' - ' + str(ct)
                        prefix += suffix
                    output[xml][prefix] = ele.text.encode('utf8')
                    PROP[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
        else:
            root = tree.getroot()
            for ele in root.iter():
                xpath = tree.getelementpath(ele)
                if 'PROCESSING' in xpath or '/data' in xpath :
                    continue
                if ele.tag in ['value', 'unit', 'description', 'type']:
                    continue
                children = extractChildren(ele)
                if 'value' in children or 'unit' in children:
                    extractVUDXpath(ele, output[xml], '')
                    if 'ID' in xpath:
                        extractVUDXpath(ele, IDS[xml], idXpath(xpath))
                    elif 'DATA_SOURCE' in xpath:
                        extractVUDXpath(ele, DAT[xml], idXpath(xpath))
                    elif 'MATERIALS' in xpath:
                        extractVUDXpath(ele, MAT[xml], idXpath(xpath))
                    elif 'CHARACTERIZATION' in xpath:
                        extractVUDXpath(ele, CHAR[xml], idXpath(xpath))
                    elif 'PROPERTIES' in xpath:
                        extractVUDXpath(ele, PROP[xml], idXpath(xpath))
                    elif 'MICROSTRUCTURE' in xpath:
                        extractVUDXpath(ele, MIC[xml], idXpath(xpath))
                if ele.text is not None:
                    # determine the prefix
                    prefix = ele.tag
                    suffix = ''
                    if prefix in output[xml]:
                        ct = 0
                        while ' - '.join([prefix, str(ct)]) in output[xml]:
                            ct += 1
                        suffix = ' - ' + str(ct)
                        prefix += suffix
                    if 'ID' in xpath:
                        IDS[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    elif 'DATA_SOURCE' in xpath:
                        DAT[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    elif 'MATERIALS' in xpath:
                        if ele.tag == 'mass' or ele.tag == 'volume':
                            prefix = ele.getparent().getparent().tag + ' - ' + prefix
                        MAT[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    elif 'CHARACTERIZATION' in xpath:
                        CHAR[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    elif 'PROPERTIES' in xpath:
                        PROP[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    elif 'MICROSTRUCTURE' in xpath:
                        MIC[xml][prefix] = (ele.text.encode('utf8'), idXpath(xpath) + suffix)
                    output[xml][prefix] = ele.text.encode('utf8')
                    
    # loop thru the top level dicts to get the mergedKey without losing the
    # order among the top level items
    mergedKeyTop = []
    for top in [IDS, DAT, MAT, PROC, CHAR, PROP, MIC]:
        # get the common keys in the xmldicts
        commonKey = []
        for key in top.values()[0]: # use the first xml dict
            uncommon = False
            for xmldict in top.values():
                if key not in xmldict:
                    uncommon = True
            if not uncommon:
                commonKey.append(key)
        # get the complete key list while reserving the order
        unmergedKey = [] # a 2d list
        for xmldict in top.values():
            unmergedKey.append(xmldict.keys())
        mergedKey = mergeList(commonKey, unmergedKey, top)
        mergedKeyTop += mergedKey
        # now fill in the uncommon keys for each xmldict
        uncommonKey = [k for k in mergedKey if k not in commonKey]
        for k in uncommonKey:
            for xmldict in output.values():
                if k not in xmldict:
                    xmldict[k] = ''
    # generate csv file
    if brief:
        filename = xmlsDir+'brief_report.csv'
    else:
        filename = xmlsDir+'full_report.csv'
    # remove the 
    with open(filename, 'wb') as f:
        writer = csv.DictWriter(f, fieldnames = mergedKeyTop)
        writer.writeheader()
        # writer.writerow({'xml directory':"Date: " + date.today().isoformat()})
        for xmldict in output.values():
            writer.writerow(xmldict)
    print 'Report generated as %s' %(filename)
    return

# helper method for extracting determined xpath elements
def extractDetXpath(eles, output_xml, prefix, tree):
    if tree == '':
        # single element
        if len(eles) == 1:
            output_xml[prefix] = eles[0].text
        return output_xml
        # multiple elements
        ct = 0 # in case of multiple Matrix
        for ele in eles:
            header = prefix + ' - ' + str(ct) # a header in the output file
            output_xml[header] = ele.text
            ct += 1
    else:    
        # single element
        if len(eles) == 1:
            output_xml[prefix] = (eles[0].text, idXpath(tree.getelementpath(eles[0])))
        return output_xml
        # multiple elements
        ct = 0 # in case of multiple Matrix
        for ele in eles:
            header = prefix + ' - ' + str(ct) # a header in the output file
            output_xml[header] = (ele.text, idXpath(tree.getelementpath(ele)) + ' - ' + str(ct))
            ct += 1
    return output_xml

# helper method for extracting xpath elements with value, unit, and description
def extractVUDXpath(ele, output_xml, xpathID):
    # determine the prefix
    prefix = ele.tag
    suffix = ''
    if prefix in output_xml:
        ct = 0
        while ' - '.join([prefix, str(ct)]) in output_xml:
            ct += 1
        suffix = ' - ' + str(ct)
        prefix += suffix
    # value and unit, type for uncertainty
    value = ''
    unit = ''
    unctype = ''
    if ele.find('value') is not None:
        value = ele.find('value').text
    if ele.find('unit') is not None:
        unit = ele.find('unit').text
    if ele.find('type') is not None:
        unctype = ele.find('type').text
    if len(value) > 0 or len(unit) > 0:
        if xpathID == '':
            output_xml[prefix] = ' '.join([unctype, value, unit])    
        else:
            output_xml[prefix] = (' '.join([unctype, value, unit]), xpathID + suffix)
    # description
    desc = ''
    if ele.find('description') is not None:
        desc = ele.find('description').text
    if len(desc) > 0:
        if xpathID == '':
            output_xml[prefix + ' - description'] = desc
        else:
            output_xml[prefix + ' - description'] = (desc, xpathID + suffix)
    return output_xml

# helper method for getting tags of all the child elements
def extractChildren(ele):
    children = []
    for e in ele.findall('./'):
        children.append(e.tag)
    return children

# helper method for merge lists while preserving the order.
# Example: [[1, 3, 7], [1, 2, 3, 7, 8]] => [1, 2, 3, 7, 8]
def mergeList(commonKey, unmergedKey, topLevelDict):
    mergedKey = [] # init
    # as long as unmergedKey has content, loop
    while len(sum(unmergedKey, [])) > 0: # flatten unmergedKey into 1d list
        # get the index in the commonKey of the first items in the nested lists
        # by default, if there is an uncommon key, the indexList will contain
        # the xpathID instead
        indexList = indexOfTwoDListHead(unmergedKey, commonKey, topLevelDict)
        indexForPop = minXpath(indexList) # find the min
        # print '========================='
        # print indexList
        # print indexForPop
        # get the indices of the nested list to poped
        indices = [i for i, x in enumerate(indexList) if x == indexForPop]
        for i in indices:
            popedKey = unmergedKey[i].pop(0)
            if popedKey not in mergedKey:
                mergedKey.append(popedKey)
    return mergedKey

# a helper method to find the "min" xpathID
def minXpath(xpathIDList):
    default = True
    xpathIDSet = set(xpathIDList)
    for xpathID in xpathIDSet:
        if ' - ' in xpathID:
            default = False
    if default:
        return min(xpathIDSet)
    sortedXpathList = sorted(list(xpathIDSet))
    # find the first dashed item and the first non dashed item
    firstDash = ''
    firstNonDash = ''
    dashed = []
    for xpathID in sortedXpathList:
        # unlike non dashed items, dashed items are not yet sorted
        if ' - ' in xpathID:
            dashed.append(xpathID)
        if ' - ' not in xpathID and firstNonDash == '':
            firstNonDash = xpathID
    dashed.sort(key=lambda x: x.split(' - ')[0])
    dashed.sort(key=lambda x: x.split(' - ')[-1])
    if len(dashed) > 0:
        firstDash = dashed[0]
    # compare firstDash and firstNonDash
    # when we have both dashed item and non dashed item, we need to use our
    # own way to find the min
    if firstDash != '' and firstNonDash != '':
        # check the chars from the beginning to the ' - ' (last char excluded)
        # i.e. check whether the two ele's have the same parent
        # examples:
        # 6102 - 0 > 6104   same 610
        # 6102 - 0 > 61023  same 610
        # 6102 - 0 < 611    610 < 611
        # 6102 - 0 < 6125   610 < 612
        firstDashPar = firstDash[:firstDash.find(' - ') - 1] # get the parent
        if len(firstDashPar) <= len(firstNonDash):
            if firstNonDash[:len(firstDashPar)] <= firstDashPar:
                return firstNonDash
            else:
                return firstDash
        else:
            if firstDashPar <= firstNonDash:
                return firstDash
            else: # not likely
                return firstNonDash
    elif firstDash != '' and firstNonDash == '':
        # first compare by the number before the dash, then compare by the 
        # number after the dash
        sortedXpathList.sort(key=lambda x: x.split(' - ')[0])
        sortedXpathList.sort(key=lambda x: x.split(' - ')[-1])
        return sortedXpathList[0]


# a helper method to get the index of the first item in each nested 1d list in a
# given 2d list according to the given indexRef by default, if there is an item
# that is not in the indexRef, the xpathID will be returned instead
def indexOfTwoDListHead(twoDList, indexRef, topLevelDict):
    heads = []
    index = []
    xpathFlag = False # a flag for return xpath
    for i in twoDList:
        if len(i) == 0:
            heads.append('')
        else:
            heads.append(i[0])
    for head in heads:
        if head == '':
            index.append(str(len(indexRef))) # a very large number
        elif head not in indexRef:
            xpathFlag = True # raise the flag
            index = [] # init index
            break
        else:
            index.append(str(indexRef.index(head)))
    if xpathFlag:
        for j in xrange(len(heads)):
            head = heads[j]
            if head == '':
                xpathID = 'EMPTY'
            else:
                xml = topLevelDict.keys()[j]
                xpathID = topLevelDict[xml][head][1]
                if head not in indexRef:
                    xpathID = '00' + xpathID # pop the uncommon keys first
            index.append(xpathID)
    return index

# a helper method to id xpath based on their order of appearance in the schema
# xpath example: 'PROPERTIES/Electrical/AC_DielectricDispersion[2]/Dielectric_Real_Permittivity/data'
def idXpath(xpath):
    myID = '' # init the id for the xpath
    tree = ET.parse('E:/Duke/DIBBS/data_update/info_update_xml/schema/PNC_schema_060718.xsd') # load the schema
    tempTree = tree.find('.//*[@name="Root"]') # this variable will go one level deeper after each iter
    names = xpath.split('/') # split the xpath
    for name in names:
        if '[' in name and name[-1] == ']':
            name = name[0:name.index('[')]
        (ele, index) = getChildNIndex(tempTree, name)
        myID += str(index) # append to myID
        # find the type of ele
        eleType = ele.get('type')
        # find the element with the name of the type we get earlier
        typePath = './/*[@name="%s"]' %(eleType)
        if name == 'Citation':
            tempTree = tree.findall(typePath)[1]
        else:
            tempTree = tree.find(typePath)
    return myID
    
# get the child element matching the given name and its index
def getChildNIndex(tempTree, name):
    index = 0
    for ele in tempTree[0].iter('{http://www.w3.org/2001/XMLSchema}element'):
        if ele.get('name') == name:
            return (ele, index)
        index += 1
    return (None, -1)

# a run function
def run(xmlsDir):
    xml_human_valid(xmlsDir, True)
    xml_human_valid(xmlsDir, False)

if __name__ == '__main__':
    xmlsDir = raw_input('Please type in the directory of the xml folder:')
    xmlsDir.replace('\\', '/')
    if len(xmlsDir) > 0 and xmlsDir[-1] != '/':
        xmlsDir += '/'
    run(xmlsDir)
    # run('./274/')
    
    # test
    # unmergedKey = [[1,2,3], [2,3,4], [7, 2,3], [7,8,2,9,3]]
    # commonKey = [2, 3]
    # assert(mergeList(commonKey, unmergedKey) == [1,7,8,2,9,3,4])
    # print 'Pass!'
    # xpath = 'PROPERTIES/Electrical/AC_DielectricDispersion[2]/Dielectric_Real_Permittivity/data'
    # xpath = 'DATA_SOURCE/Citation/CommonFields/DOI'
    # print idXpath(xpath)
    # xpathIDList = ['6102 - 2', '6101 - 1', '7120 - 0', '6102 - 0', '6102 - 1']
    # assert(minXpath(xpathIDList) == '6102 - 0')
    # xpathIDList = ['6102 - 2', '6101 - 1', '7120 - 0', '6102 - 0', '6109']
    # assert(minXpath(xpathIDList) == '6109')
    # xpathIDList = ['6102 - 2', '6101 - 1', '7120 - 0', '6102 - 0', '6109', '91']
    # assert(minXpath(xpathIDList) == '6109')
    # xpathIDList = ['6102 - 2', '6101 - 1', '7120 - 0', '6102 - 0', '62']
    # assert(minXpath(xpathIDList) == '6102 - 0')
    # print "Tests passed for minXpath()!"