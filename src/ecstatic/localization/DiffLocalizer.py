import sys
import os
import json
import logging
from src.ecstatic.localization.AbstractLocalization import AbstractLocalization;
from src.ecstatic.localization.LocalizeResult import LocalizeResult;
class DiffLocalizer(AbstractLocalization):


    def __init__(self,violations):
        self.violations=violations;

    def get_fragmentation_for_file(self,fDict):
        classmap = dict();
        for x in fDict:
            classN = x.split(":")[0]
            anonymousClassCutOff = len(classN);
            if "$" in classN:
                anonymousClassCutOff = classN.index("$")
            classN = classN[0:anonymousClassCutOff]
            if classmap.get(classN) is not None:
                #we've seen this class b4
                classmap[classN] = classmap[classN] + fDict[x]
            else:
                classmap[classN] = fDict[x];
        return classmap;

    def get_dict_for_file(self,file_lines):
        rDict = dict()
        for x in file_lines:
            line = x.split(":")
            if rDict.get(line[1]+":"+line[2]) is not None:
                #we've seen this line before inc count
                rDict[line[1]+":"+line[2]] = rDict[line[1]+":"+line[2]]+1
            else:
                rDict[line[1]+":"+line[2]] = 1;
        return rDict;
    linesForFile = dict();
    def get_diff_for_files(self,file1,file2,partial_order,apk, violated):
        f1_lines = []
        f2_lines = []

        if(file1 not in lineForFile):
            with open(file1,'r') as fp:
                linesForFile[file1] = self.get_dict_for_file(fp.readlines())
        if(file2 not in linesForFile):
            with open(file2,'r') as fp:
                linesForFile[file2] = self.get_dict_for_file(fp.readlines())
        f1_dict = linesForFile[file1];
        f2_dict = linesForFile[file2];

        rList = []
        #TODO::.keys method
        # 1 -> 2, A -> B
        diffDict = dict();
        diffInfo="";
        for x in f2_dict:
            if x not in f1_dict:
                diffInfo+=x.strip()+":"+str(f2_dict[x])+"\n";
                diffDict[x] = f2_dict[x]
        #fragmentation = self.get_fragmentation_for_file(diffDict);
        fragmentation = None;
        return LocalizeResult(diffInfo,apk,partial_order,fragmentation,diffDict,violated);


    def localize(self):
        #Internal logic for running this localizer
        logging.warning("Started Localize")
        #go through all violations and check em out
        rList: List[LocalizeResult] = []
        for x in self.violations:
            #we are interested in a couple things, mostly
            # the apk
            # the two files that contain instrumentation info
            # the partial_orders being bad
            first =False;
            for pO in x.partial_orders:
                target = x.job1.job.target.name
                target = target[target.rindex("/")+1:];

                job1 = x.job1.results_location.replace(".apk.raw",".apk.xml.flowdroid.result.instrumentation")
                job2 = x.job2.results_location.replace(".apk.raw",".apk.xml.flowdroid.result.instrumentation")

                split = job1.split("/");

                inst_file_1 = "";
                i=0;
                for st in split:
                    if i == 5:
                        inst_file_1+="/xml_scripts"
                    inst_file_1+="/"+st;
                    i+=1;

                inst_file_1=inst_file_1[1:];

                split=job2.split("/");
                inst_file_2 = "";
                i=0;
                for st in split:
                    if i==5:
                        inst_file_2+="/xml_scripts"
                    inst_file_2+="/"+st;
                    i+=1;
                inst_file_2=inst_file_2[1:]
                lineDiff="";
                if not first:
                    rList.append(self.get_diff_for_files(inst_file_2,inst_file_1,pO,target,x.violated))
                else:
                    rList.append(self.get_diff_for_files(inst_file_1,inst_file_2,pO,target,x.violated))
                first = True
        return rList;
