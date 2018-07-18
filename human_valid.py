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
                                          output[xml], 'Control ID')
            IDS[xml] = extractDetXpath(tree.findall('.//Control_ID'),
                                       IDS[xml], 'Control ID')
            # matrix name
            output[xml] = extractDetXpath(tree.findall('.//MatrixComponent/ChemicalName'),
                                          output[xml], 'Matrix')
            MAT[xml] = extractDetXpath(tree.findall('.//MatrixComponent/ChemicalName'),
                                       MAT[xml], 'Matrix')
            # filler name
            output[xml] = extractDetXpath(tree.findall('.//FillerComponent/ChemicalName'),
                                          output[xml], 'Filler')
            MAT[xml] = extractDetXpath(tree.findall('.//FillerComponent/ChemicalName'),
                                       MAT[xml], 'Filler')
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
                MAT[xml][prefix] = mfvf.text
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
                    extractVUDXpath(ele, output[xml])
                    extractVUDXpath(ele, PROP[xml])
                if ele.text is not None:
                    # determine the prefix
                    prefix = ele.tag
                    if prefix in output[xml]:
                        suffix = 0
                        while ' - '.join([prefix, str(suffix)]) in output[xml]:
                            suffix += 1
                        prefix = ' - '.join([prefix, str(suffix)])
                    output[xml][prefix] = ele.text.encode('utf8')
                    PROP[xml][prefix] = ele.text.encode('utf8')
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
                    extractVUDXpath(ele, output[xml])
                    if 'ID' in xpath:
                        extractVUDXpath(ele, IDS[xml])
                    elif 'DATA_SOURCE' in xpath:
                        extractVUDXpath(ele, DAT[xml])
                    elif 'MATERIALS' in xpath:
                        extractVUDXpath(ele, MAT[xml])
                    elif 'CHARACTERIZATION' in xpath:
                        extractVUDXpath(ele, CHAR[xml])
                    elif 'PROPERTIES' in xpath:
                        extractVUDXpath(ele, PROP[xml])
                    elif 'MICROSTRUCTURE' in xpath:
                        extractVUDXpath(ele, MIC[xml])
                if ele.text is not None:
                    # determine the prefix
                    prefix = ele.tag
                    if prefix in output[xml]:
                        suffix = 0
                        while ' - '.join([prefix, str(suffix)]) in output[xml]:
                            suffix += 1
                        prefix = ' - '.join([prefix, str(suffix)])
                    if 'ID' in xpath:
                        IDS[xml][prefix] = ele.text.encode('utf8')
                    elif 'DATA_SOURCE' in xpath:
                        DAT[xml][prefix] = ele.text.encode('utf8')
                    elif 'MATERIALS' in xpath:
                        if ele.tag == 'mass' or ele.tag == 'volume':
                            prefix = ele.getparent().getparent().tag + ' - ' + prefix
                        MAT[xml][prefix] = ele.text.encode('utf8')
                    elif 'CHARACTERIZATION' in xpath:
                        CHAR[xml][prefix] = ele.text.encode('utf8')
                    elif 'PROPERTIES' in xpath:
                        PROP[xml][prefix] = ele.text.encode('utf8')
                    elif 'MICROSTRUCTURE' in xpath:
                        MIC[xml][prefix] = ele.text.encode('utf8')
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
        mergedKey = mergeList(commonKey, unmergedKey)
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
    with open(filename, 'wb') as f:
        writer = csv.DictWriter(f, fieldnames = mergedKeyTop)
        writer.writeheader()
        # writer.writerow({'xml directory':"Date: " + date.today().isoformat()})
        for xmldict in output.values():
            writer.writerow(xmldict)
    print 'Report generated as %s' %(filename)
    return

# helper method for extracting determined xpath elements
def extractDetXpath(eles, output_xml, prefix):
    # single element
    if len(eles) == 1:
        output_xml[prefix] = eles[0].text
    return output_xml
    # multiple elements
    ct = 0 # in case of multiple Matrix
    for ele in eles:
        header = prefix + '-' + str(ct) # a header in the output file
        output_xml[header] = ele.text
        ct += 1
    return output_xml

# helper method for extracting xpath elements with value, unit, and description
def extractVUDXpath(ele, output_xml):
    # determine the prefix
    prefix = ele.tag
    if prefix in output_xml:
        suffix = 0
        while ' - '.join([prefix, str(suffix)]) in output_xml:
            suffix += 1
        prefix = ' - '.join([prefix, str(suffix)])
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
        output_xml[prefix] = ' '.join([unctype, value, unit])
    # description
    desc = ''
    if ele.find('description') is not None:
        desc = ele.find('description').text
    if len(desc) > 0:
        output_xml[prefix + ' - description'] = desc
    return output_xml

# helper method for getting tags of all the child elements
def extractChildren(ele):
    children = []
    for e in ele.findall('./'):
        children.append(e.tag)
    return children

# helper method for merge lists while preserving the order.
# Example: [[1, 3, 7], [1, 2, 3, 7, 8]] => [1, 2, 3, 7, 8]
def mergeList(commonKey, unmergedKey):
    mergedKey = [] # init
    # as long as unmergedKey has content, loop
    while len(sum(unmergedKey, [])) > 0: # flatten unmergedKey into 1d list
        # get the index in the commonKey of the first items in the nested lists
        indexList = indexOfTwoDListHead(unmergedKey, commonKey)
        # always add uncommon keys to the mergedKey before common keys
        indexForPop = min(indexList) # find the min
        # get the indices of the nested list to poped
        indices = [i for i, x in enumerate(indexList) if x == indexForPop]
        for i in indices:
            popedKey = unmergedKey[i].pop(0)
            if popedKey not in mergedKey:
                mergedKey.append(popedKey)
    return mergedKey

# helper method to get the index of the first item in each nested 1d list in a
# given 2d list according to the given indexRef
def indexOfTwoDListHead(twoDList, indexRef):
    heads = []
    index = []
    for i in twoDList:
        if len(i) == 0:
            heads.append('')
        else:
            heads.append(i[0])
    for head in heads:
        if head == '':
            index.append(len(indexRef)) # a very large number
        elif head not in indexRef:
            index.append(-1)
        else:
            index.append(indexRef.index(head))
    return index

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
    
    # test
    # unmergedKey = [[1,2,3], [2,3,4], [7, 2,3], [7,8,2,9,3]]
    # commonKey = [2, 3]
    # assert(mergeList(commonKey, unmergedKey) == [1,7,8,2,9,3,4])
    # print 'Pass!'



