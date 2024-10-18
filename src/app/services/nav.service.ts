import { Injectable } from '@angular/core';
import { post } from 'aws-amplify/api';
import { PageCard } from '../models/page-card.model';

@Injectable({
  providedIn: 'root'
})
export class NavService {
    private filterValueDictionary: {
        "all": {}
    };

    
    async getCardsByParams(params: any): Promise<any> {
        try {
        //   console.log('Getting product by card:', pgid);
          const { body } = await post({
            apiName: 'tezbuildpublic',
            path: `/nav`,
            options: {
              headers: {
                'Content-Type': 'application/json',
              },
              body: {
                "action": "getPageCardsByAggregations",
                "params": params
              }
            }
          }).response;
          const response = await body.json();
          // Ensure response is an object
          if (typeof response === 'object') {
              const res = {};
              res['total'] = JSON.parse(response['body'])['paginationToken'];
              res['cards'] = JSON.parse(response['body'])['cards'].map((card: any) => {
                  return new PageCard(card.id, card.heading, card.type, card.subheading, card.image);
              });
              res['title'] = JSON.parse(response['body'])['title'];
              res['filters'] =  JSON.parse(response['body'])['filters'];
              res['aggregations'] =  JSON.parse(response['body'])['aggregations'];
              return res;
          } else {
              console.error('Invalid response format or empty response:', response);
          }
      } catch (error) {
          console.error('Error invoking API:', error);
      }
      return null;
       
    }

    async getCardsByFilters(params: any): Promise<any> {
        try {
        //   console.log('Getting product by card:', pgid);
          const { body } = await post({
            apiName: 'tezbuildpublic',
            path: `/nav`,
            options: {
              headers: {
                'Content-Type': 'application/json',
              },
              body: {
                "action": "getPageCardsByParams",
                "params": params
              }
            }
          }).response;
          const response = await body.json();
          // Ensure response is an object
          if (typeof response === 'object') {
              const res = {};
              res['total'] = JSON.parse(response['body'])['paginationToken'];
              res['cards'] = JSON.parse(response['body'])['cards'].map((card: any) => {
                  return new PageCard(card.id, card.heading, card.type, card.subheading, card.image);
              });
              res['title'] = JSON.parse(response['body'])['title'];
            //   res['filters'] =  JSON.parse(response['body'])['filters'];
            //   res['aggregations'] =  JSON.parse(response['body'])['aggregations'];
              return res;
          } else {
              console.error('Invalid response format or empty response:', response);
          }
      } catch (error) {
          console.error('Error invoking API:', error);
      }
      return null;
       
    }

    async getCardsByNavParams(params: any): Promise<any> {
        try {
            console.log('Getting nav page:', params);
            const { body } = await post({
            apiName: 'tezbuildpublic',
            path: `/nav`,
            options: {
                headers: {
                    'Content-Type': 'application/json',
                },
                body: {
                    "action": "getPageCardsByNavParams",
                    "params": params
                }
            }
            }).response;
            const response = await body.json();
            // Ensure response is an object
            if (typeof response === 'object') {
                const res = {};
                res['total'] = JSON.parse(response['body'])['paginationToken'];
                console.log(JSON.parse(response['body'])['cards']);
                res['cards'] = JSON.parse(response['body'])['cards'].map((card: any) => {
                    return new PageCard(card.id, card.heading, card.type, card.subheading, card.image);
                });
                res['title'] = JSON.parse(response['body'])['title'];
                res['filters'] =  JSON.parse(response['body'])['filters'];
                return res;
            } else {
                console.error('Invalid response format or empty response:', response);
            }
        } catch (error) {
            console.error('Error invoking API:', error);
        }
        return null;
    }
    async getCardsByHomeParams(params: any): Promise<any> {
        try {
            console.log('Getting nav page:', params);
            const { body } = await post({
            apiName: 'tezbuildpublic',
            path: `/nav`,
            options: {
                headers: {
                    'Content-Type': 'application/json',
                },
                body: {
                    "action": "getPageCardsByHome",
                    "params": params
                }
            }
            }).response;
            const response = await body.json();
            // Ensure response is an object
            if (typeof response === 'object') {
                const res = {};
                res['total'] = JSON.parse(response['body'])['paginationToken'];
                console.log(JSON.parse(response['body'])['cards']);
                res['cards'] = JSON.parse(response['body'])['cards'].map((card: any) => {
                    return new PageCard(card.id, card.heading, card.type, card.subheading, card.image);
                });
                res['title'] = JSON.parse(response['body'])['title'];
                res['filters'] =  JSON.parse(response['body'])['filters'];
                return res;
            } else {
                console.error('Invalid response format or empty response:', response);
            }
        } catch (error) {
            console.error('Error invoking API:', error);
        }
        return null;
    }
}