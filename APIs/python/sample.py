#! /usr/bin/python3

### REQUIRES python 3 !!!!

## Run:  ./sample.py file_in file_out
## For example:
##     ./sample.py test.txt test_out.txt

import freeling
import sys

## ------------  output a parse tree ------------
def printTree(ptree, depth):

    node = ptree.begin();

    print(''.rjust(depth*2),end='');
    info = node.get_info();
    if (info.is_head()): print('+',end='');

    nch = node.num_children();
    if (nch == 0) :
        w = info.get_word();
        print ('({0} {1} {2})'.format(w.get_form(), w.get_lemma(), w.get_tag()),end='');

    else :
        print('{0}_['.format(info.get_label()));

        for i in range(nch) :
            child = node.nth_child_ref(i);
            printTree(child, depth+1);

        print(''.rjust(depth*2),end='');
        print(']',end='');

    print('');

## ------------  output a parse tree ------------
def printDepTree(dtree, depth):

    node = dtree.begin()

    print(''.rjust(depth*2),end='');

    info = node.get_info();
    link = info.get_link();
    linfo = link.get_info();
    print ('{0}/{1}/'.format(link.get_info().get_label(), info.get_label()),end='');

    w = node.get_info().get_word();
    print ('({0} {1} {2})'.format(w.get_form(), w.get_lemma(), w.get_tag()),end='');

    nch = node.num_children();
    if (nch > 0) :
        print(' [');

        for i in range(nch) :
            d = node.nth_child_ref(i);
            if (not d.begin().get_info().is_chunk()) :
                printDepTree(d, depth+1);

        ch = {};
        for i in range(nch) :
            d = node.nth_child_ref(i);
            if (d.begin().get_info().is_chunk()) :
                ch[d.begin().get_info().get_chunk_ord()] = d;

        for i in sorted(ch.keys()) :
            printDepTree(ch[i], depth + 1);

        print(''.rjust(depth*2),end='');
        print(']',end='');

    print('');



## ----------------------------------------------
## -------------    MAIN PROGRAM  ---------------
## ----------------------------------------------

## Modify this line to be your FreeLing installation directory
FREELINGDIR = "/usr/local";

DATA = FREELINGDIR+"/share/freeling/";
LANG="es";

freeling.util_init_locale("default");

# create language analyzer
la=freeling.lang_ident(DATA+"common/lang_ident/ident.dat");

# create options set for maco analyzer. Default values are Ok, except for data files.
op= freeling.maco_options(LANG);  # maco (Morphological Analyzer) options object
op.set_data_files( "",  # User Map module
                   DATA + "common/punct.dat",  # punctuation
                   DATA + LANG + "/dicc.src",  # Dictionary Search module: lemmas and PoS tags
                   DATA + LANG + "/afixos.dat",  # affixation rules (used by Dictionary Search module)
                   "",  # compounding rules (used by Dictionary Search module)
                   DATA + LANG + "/locucions.dat",  # multiword
                   DATA + LANG + "/np.dat",  # Named Entity recognition
                   DATA + LANG + "/quantities.dat",  # depends on number detecion module
                   DATA + LANG + "/probabilitats.dat");  # needed for PoS later

# create analyzers
tk=freeling.tokenizer(DATA+LANG+"/tokenizer.dat");
sp=freeling.splitter(DATA+LANG+"/splitter.dat");
sid=sp.open_session();  # open a splitting session
mf=freeling.maco(op);  # creates Morphological Analyzer with maco_options object options

# activate mmorpho odules to be used in next call
mf.set_active_options(False, True, True, True,  # select which among created
                      True, True, False, True,  # submodules are to be used.
                      True, True, True, True ); # default: all created submodules are used

# create tagger, sense anotator, and parsers
tg=freeling.hmm_tagger(DATA+LANG+"/tagger.dat",True,2);  # classical trigram Markovian tagger
# True: words that carry retokenization mark (set by dictionary or affix handling modules)
# will be retokenized after tagging. Apparently, already retokenized by Dictionary Module (as per manual)
# 2: if ambiguos, force selection after retokenization
sen=freeling.senses(DATA+LANG+"/senses.dat");  # returns list of senses for each lemma
parser= freeling.chart_parser(DATA+LANG+"/chunker/grammar-chunk.dat");  # enriches each sentence object with a parse_tree object, whose leaves have a link to the sentence words.
# chart_parser.get_start_symbol returns the initial symbol of the grammar, which is needed by the dependency parser.
dep=freeling.dep_txala(DATA+LANG+"/dep_txala/dependences.dat", parser.get_start_symbol()); # Rule-based Dependency Parser

file_in = open(sys.argv[1])
file_out = open(sys.argv[2], 'w')
# process input text
lin=file_in.readline();

print ("Text language is: "+la.identify_language(lin)+"\n");
# here it uses just first line for language detection

while (lin) :
    l = tk.tokenize(lin);
    ls = sp.split(sid,l,False);  # False: don't flush buffer; wait to see
    # what comes next (in next line input)

    ls = mf.analyze(ls);  # Morphological Analyzer
    # Phonetical encoding and alternative suggestion modules may be included
    # for possibly mispelled words by children here.
    ls = tg.analyze(ls);  # it seems to fail if run without mf analysis first
    # what adds the above? I'm not sure what it adds if retokenization is delete_TreeOfNode
    # at the MF step

    ls = sen.analyze(ls);  # sense annotator, to associate to each word its possible WordNet synsets
    ls = parser.analyze(ls);  # parse tree: ordered, rooted tree that represents the syntactic structure of a string
    ls = dep.analyze(ls);

    ## output results
    for s in ls :
       ws = s.get_words();
       for w in ws :
          print(w.get_form()+" "+w.get_lemma()+" "+w.get_tag()+" "+w.get_senses_string());
          # for some reason, senses (synsets) were not ranked (number between ":" and follwing "/")
       print ("");
       import pdb
       pdb.set_trace()

       tr = s.get_parse_tree();
       printTree(tr, 0);

       dp = s.get_dep_tree();
       printDepTree(dp, 0)

    lin=file_in.readline();

# clean up
sp.close_session(sid);

file_in.close()
file_out.close()
