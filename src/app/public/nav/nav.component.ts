import { Attribute, Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormControl, FormGroup, FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { LoadingComponent } from '../loading/loading.component';
import { NavService } from '../../services/nav.service';
import { PageCard } from '../../models/page-card.model';
import { Filters } from '../../models/filters.model';
import { ReactiveFormsModule } from '@angular/forms';
import { PaginationComponent } from "../pagination/pagination.component";
import { ProductComponent } from '../product/product.component';
import { MatSliderModule } from '@angular/material/slider';
import {MatSelectModule} from '@angular/material/select';

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, LoadingComponent, ReactiveFormsModule, PaginationComponent, ProductComponent,MatSliderModule,MatSelectModule],
  templateUrl: './nav.component.html',
  styleUrls: ['./nav.component.scss']
})
export class NavComponent implements OnInit {
  link: string;
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private navService: NavService
  ) {
    this.filterForm = new FormGroup({});
    this.SheetGoodfilterForm = new FormGroup({});
  }


  searchForm: FormGroup = new FormGroup({
    searchInput: new FormControl('')
  })

  currentPage: number = 1; // pagination currentPage number
  navId: number;
  limit: number = 10; // limit for number of records 
  total: number = 0; // pagination total elements
  filterForm: FormGroup;
  SheetGoodfilterForm: FormGroup;
  isLumber: boolean = false; // flag for displaying the filter options for Lumber category
  isSheetGood: boolean = false; // flag for displaying the filter options for Sheet Good category
  page: string; // nav page or search
  id: string; // id of the nav page
  searchTerm: string; // search term from query string
  filters: Filters; // filters, which should be null if filtering is not allowed
  title: string; // title of the page
  options: string[] = [];
  cards: PageCard[] = []; // cards to display on the page
  cardss: any[] = [];
  isLoading: boolean = true;
  isDataFetched: boolean = false; // flag to display the pagination
  isLoad: boolean = false; // flag to show the loader between api calls
  inputFilters: any[] = [];
  inputFiltersSheetGood : any[] = [];
  keys: any[] = [];
  objValues: any[] = [];
  async ngOnInit() {


    this.page = this.route.snapshot.url[0].path;
    this.options.push('Lumber');
    this.options.push('Sheet Good');
    

   /* this.filterForm.valueChanges.subscribe(values => {
      const formVal=this.filterForm.value;
    });
    this.SheetGoodfilterForm.valueChanges.subscribe(values => {
      console.log(values); // Logs the current values of the form controls
    });*/

    this.searchForm.valueChanges.subscribe(values => {
      this.currentPage = 1;
    })

    this.filterForm.get('Length')?.valueChanges.subscribe(value => {
      this.onSliderChange(value);
    });
    // navId is a query string param, as is searchTerm
    // the backend will return a list of cards AND the pageType to be set as this.page
    // a valid navId will trump a seachTerm, and filters will be applied on the backend if valid
    // filters will simply be ignored by id-based pages
    // a nav page with no query string params will be treated as a search page
    // the backend will return a corrected URL in cases where the URL has an incorrect param
    // the backend is responsible for combining filters from the frontend and default filters and sending them back

    this.route.paramMap.subscribe(async params => {
      if (Object.keys(params).length) {
        this.isLoading = true;
        this.searchTerm = params.get('searchTerm') ? decodeURIComponent(params.get('searchTerm')) : '';
        if (params.get('id')) {
          await this.loadNavPage(params);
        }
        if (this.searchTerm) {
          await this.loadSearchPage(this.searchTerm);
        }

      }

      this.isLoading = false;
    });

    this.route.queryParamMap.subscribe(async params => {

      if (Object.keys(params).length) {
        this.isLoading = true;
        this.searchTerm = params.get('searchTerm') ? decodeURIComponent(params.get('searchTerm')) : '';
        if (params.get('id')) {
          await this.loadNavPage(params);
        }
        if (this.searchTerm) {
          await this.loadSearchPage(this.searchTerm);
        }

      }

      this.isLoading = false;
    });


    this.isLoading = false;
  }

  // Attributes for filters
  IdentifyingAttributes = {
    "Lumber": ['Length', 'Profile', 'Grade', 'Species', 'FingerJoint', 'Precision', 'Treatment', 'Brand'],
    "SheetGood": ['Length', 'Width', 'Thickness', 'Species', 'Grade', 'PanelType', 'Treatment', 'Edge', 'Finish', 'Brand', 'Origin', 'Metric']
  };

  async loadNavPage(params: any) {
    this.isLoad = true; // Showing the loader 
    this.cards = [];
    this.navId = params.get('id');
    let query = {
      "navId": this.navId
    }
    const res = await this.navService.getCardsByNavParams(query);
    this.loadCards(res)
    this.isLoad = false; // hiding the loader upon fetching data from api
    this.isDataFetched = true; // displaying the pagination 
  }

async loadSearchPage(params: any) {
    this.isLoad = true; // Showing the loader 
    this.cards = [];
    let query = {
      "limit": this.limit,
      "page": this.currentPage,
      "searchTerm": params
    }
    const category = this.searchForm.get('searchInput').value;
    const res = await this.navService.getCardsByFilters(query);
    this.total = res['total'];
    this.loadCards(res)
    this.isLoad = false; // hiding the loader upon fetching data from api
    this.isDataFetched = true;

  }

//Executes on search 
  async onSearch() {
    if (this.isLoad) {
      return;  // Prevent multiple submissions
    }
    this.isLoad = true; // Showing the loader 
    this.cards = [];
    const searchTerm = this.searchForm.get('searchInput').value;
    this.loadSearchPage(searchTerm)
  }

//Executes when searching by Category
  async categorySearch(category) {
    if (this.isLoad) {
      return;  // Prevent multiple submissions
    }
    this.isLoad = true; // Showing the loader 
    this.cards = [];
    const searchTerm = this.searchForm.get('searchInput').value;
   
    const query = {
      limit: this.limit,
      page: this.currentPage,
      category: category,
      aggr: this.isLumber?this.IdentifyingAttributes.Lumber:this.IdentifyingAttributes.SheetGood
     
    };
    if(this.isLumber){
       for(const attribute of this.IdentifyingAttributes.Lumber){
         
         if (this.filterForm.value[attribute]) {
           query[attribute] =(this.filterForm.value[attribute]);
         }
       }
     }
     else{
       for(const attribute of this.IdentifyingAttributes.SheetGood){
       
         if (this.SheetGoodfilterForm.value[attribute]) {
           query[attribute] =(this.SheetGoodfilterForm.value[attribute]);
         }
       }
     }
     console.log(query)
    const res = await this.navService.getCardsByParams(query);
    this.total = res['total'];
    this.loadCards(res)
    this.loadFilters(res)
    this.isLoad = false; // hiding the loader upon fetching data from api
    this.isDataFetched = true;
  }


//Load Page cards
  loadCards(res: any) {
    this.cards = [];
    this.title = res.title;
    for (let i = 0; i < res.cards.length; i++) {
      const result = res.cards[i];
     
      // Construct the card object
      let a = {
        'id': result.id,
        'type': result.species, // Use species from the result
        'image': result.image, // Use image from the result
        'title': result.title, // Use heading for title
        'subtitle': result.subtitle, // Use subheading
        'link': result.link,
      };
      this.cards.push(a);
    }
    if (res.filters) {
      this.filters = res.filters;
      // res.filters are considered the "default" filters because they are inherited from the nav page
    }
  }

//Load Aggregation Filters
  loadFilters(res) {
     // Clear previous controls
     
    this.inputFilters = []; // Clear previous filters
    this.inputFiltersSheetGood=[];
    this.keys = Object.keys(res['aggregations']);
    console.log(this.keys)
    this.objValues = Object.values(res['aggregations']);
    for (let i = 0; i < this.keys.length; i++) {
    
      if (this.objValues[i].type == 'slider') {
        let a = {
          'field': this.keys[i],
          'fieldType': this.objValues[i].type,
          'min': this.objValues[i].min,
          'max': this.objValues[i].max,
          'avg': this.objValues[i].avg
        }
        if(this.isLumber){this.inputFilters.push(a);}
        else {this.inputFiltersSheetGood.push(a);}
        
      }
      else if (this.objValues[i].type == 'dropdown') {
        let a = {
          'field': this.keys[i],
          'fieldType': this.objValues[i].type,
          'values': this.objValues[i].values
        }
        if(this.isLumber){this.inputFilters.push(a);}
        else {this.inputFiltersSheetGood.push(a);}
      }


    }
    console.log(this.inputFilters)
  }

searchProducts(event: Event) {
    event.preventDefault();
    const encodedSearchTerm = encodeURIComponent(this.searchTerm);
    this.router.navigate(['/search'], { queryParams: { searchTerm: encodedSearchTerm } });
  }

  // Pagination page change

  changePage(page: number): void {
    this.currentPage = page;
    this.onSearch();

  }

  // onSelectChange -->  Invokes upon change in filter options selection 

  selectedOption: string = '';
  filteredSelectedOption: string = '';

  onCategoryChange() {
    this.currentPage = 1;
  }

 resetForm() {
    this.filterForm.reset();
    this.SheetGoodfilterForm.reset();
  }
  

  onSelectChange() {
    this.isLoad = false;
    this.currentPage = 1;
    if (this.selectedOption === 'Lumber') {
      this.toggleCategory('Lumber');
    }
    else if (this.selectedOption === 'Sheet Good') {
      this.toggleCategory('Sheet Good');
    }
    this.searchForm.patchValue({ searchInput: this.selectedOption });
    this.categorySearch(this.selectedOption);
  }

  toggleCategory(category: string) {
    if(category === 'Lumber'){
    this.isLumber = true
    this.isSheetGood = false
    } else {
    this.isSheetGood = true
    this.isLumber = false}
    this.initializeForm();
  }

  initializeForm() {
    // Clear previous controls
    this.resetForm();
    
    
    // Add controls for selected category
    if(this.isLumber){
    const selectedAttributes = this.IdentifyingAttributes.Lumber ;
    selectedAttributes.forEach(attribute => {
      this.filterForm.addControl(attribute, new FormControl(''));
    });
  } else {
      const selectedAttributesSG = this.IdentifyingAttributes.SheetGood;
      selectedAttributesSG.forEach(attribute => {
        this.SheetGoodfilterForm.addControl(attribute, new FormControl(''));
      });
      console.log('SheetGoodfilterForm controls:', this.SheetGoodfilterForm.controls);
    }
  }

  onSliderChange(value: number) {
    console.log('Slider value changed:', value);
    const formVal=this.filterForm.value;
    console.log(formVal);
    // Add any additional logic you want to handle on change here
    this.onFiltersSearch();
  }

  async onFiltersSearch(){
    console.log("Inside onFilterSearch")
    this.isDataFetched = false;
    const searchTerm = this.searchForm.get('searchInput').value;
    const query = {
      limit: this.limit,
      page: this.currentPage,
      category : this.isLumber?"Lumber":"Sheet Good"
    };
    if(this.isLumber){
     
      for(const attribute of this.inputFilters){
        
        if (this.filterForm.value[attribute['field']]) {
          console.log("Filter attribute:"+attribute['field']);
          query[attribute['field']] =(this.filterForm.value[attribute['field']]);
        }
      }} else { for(const attribute of this.inputFiltersSheetGood){
        console.log("Filter attribute:"+attribute['field']);
        if (this.SheetGoodfilterForm.value[attribute['field']]) {
          console.log("Filter attribute:"+attribute['field']);
          query[attribute['field']] =(this.SheetGoodfilterForm.value[attribute['field']]);
        }
      }

      }
      const res = await this.navService.getCardsByFilters(query);
      this.total = res['total'];
      this.loadCards(res)
      this.isDataFetched = true;
    
  }


}
